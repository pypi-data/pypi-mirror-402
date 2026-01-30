import os
import re
import time
from collections import OrderedDict
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable, Dict, Generator, List, Optional

from dateutil import parser as date_parser

try:
    from aliyun.log import GetHistogramsRequest, GetLogsRequest, LogClient
except ImportError:
    pass

from recurvedata.pigeon.dumper.base import BaseDumper
from recurvedata.pigeon.handler.base import HandlerFactory

# Constants
SQL_PATTERN = re.compile(r"^\s*select\s+.+\s+from\s+.+", re.IGNORECASE)
LOGSEARCH_ANALYSIS_PATTERN = re.compile(r".*\|\s*select\s+.+", re.IGNORECASE)

# Configuration constants
DEFAULT_TIMEZONE_OFFSET = 8  # CST (UTC+8)
TIMEZONE_ENV_VAR = "TZ_OFFSET"
LARGE_DATASET_THRESHOLD = 500_000  # 500k logs
DEFAULT_BATCH_SIZE = 1000
MAX_RETRIES = 3


def with_retry(max_retries: int = MAX_RETRIES):
    """Decorator to add retry logic with Aliyun SLS error handling."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: "AliyunSLSDumper", *args: Any, **kwargs: Any) -> Any:
            retry_count = 0

            while retry_count < max_retries:
                try:
                    return func(self, *args, **kwargs)
                except Exception as e:
                    retry_count = self.handle_aliyun_error(e, retry_count, max_retries)
                    if retry_count >= max_retries:
                        self.logger.error(f"Max retries reached for {func.__name__}, stopping: {e}")
                        raise e
            return None

        return wrapper

    return decorator


class AliyunSLSDumper(BaseDumper):
    """Used to dump data from Aliyun SLS to local file (csv format).

    This dumper uses histograms API to get total log count first, then chooses the optimal
    fetching method based on data volume:
    - For datasets > 500k logs: Uses get_log_all method (recommended by Aliyun SDK)
    - For smaller datasets: Uses standard pagination with 1000-item batches

    Args:
        access_key_id: Aliyun Access Key ID
        access_key_secret: Aliyun Access Key Secret
        endpoint: Aliyun SLS Endpoint
        project: Aliyun SLS Project
        logstore: Aliyun SLS Logstore
        start_time: Aliyun SLS Start Time (format: YYYY-MM-DD HH:MM:SS)
        end_time: Aliyun SLS End Time (format: YYYY-MM-DD HH:MM:SS)
        query: Aliyun SLS Query
        handler_factories: List of handler factories for processing data
        fields: Comma-separated list of fields to extract
    """

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        endpoint: str,
        project: str,
        logstore: str,
        start_time: str,
        end_time: str,
        query: Optional[str] = None,
        handler_factories: Optional[List[HandlerFactory]] = None,
        fields: Optional[str] = None,
    ):
        super().__init__(handler_factories=handler_factories)

        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.endpoint = endpoint
        self.project = project
        self.logstore = logstore
        self.query = query
        self.fields = [field.strip() for field in fields.split(",")] if fields else []

        # Parse time strings to datetime objects
        self.start_time = self._parse_time_string(start_time)
        self.end_time = self._parse_time_string(end_time)

        # Initialize client in fetch_logs_segment to handle import errors
        self.client = LogClient(self.endpoint, self.access_key_id, self.access_key_secret)

    def _parse_time_string(self, time_str: str) -> datetime:
        """Parse time string to datetime object using dateutil.parser."""
        try:
            parsed_time = date_parser.parse(time_str, dayfirst=False, yearfirst=True)

            if parsed_time.tzinfo is not None:
                parsed_time = parsed_time.replace(tzinfo=None)

            self.logger.info(f"Parsed '{time_str}' -> {parsed_time}")
            return parsed_time

        except (ValueError, TypeError) as e:
            raise ValueError(f"Unable to parse time string '{time_str}': {e}")

    def execute(self):
        self.meta.mark_start()
        self.execute_impl()
        self.meta.mark_finish()
        self.logger.info("dumper meta: %s", self.meta.to_json(indent=2))
        return self.meta

    def is_sql_or_logsearch_query(self, q: str) -> bool:
        if not q:
            return False
        q = q.strip()
        return bool(SQL_PATTERN.match(q) or LOGSEARCH_ANALYSIS_PATTERN.match(q))

    def _process_log_contents(self, log, raw_contents):
        """Process log contents and return ordered dictionary if fields are specified."""
        if not self.fields:
            return raw_contents

        ordered_contents: OrderedDict = OrderedDict()
        # Add fields in the user-specified order first
        for field in self.fields:
            if field in raw_contents:
                ordered_contents[field] = raw_contents[field]
            elif field == "__time__":
                # Handle time field specially
                ordered_contents[field] = log.get_time()
            elif field == "_source_":
                # Handle source field specially
                ordered_contents[field] = log.get_source()
            else:
                self.logger.warning(f"Field '{field}' not found in raw_contents and not a special field")

        return ordered_contents

    def _get_timezone_offset(self) -> int:
        """Get local timezone offset in hours from environment variable."""
        tz_offset = os.environ.get(TIMEZONE_ENV_VAR)
        return int(tz_offset) if tz_offset is not None else DEFAULT_TIMEZONE_OFFSET

    def _calculate_utc_timestamp(self, dt: datetime) -> int:
        """Calculate UTC timestamp by treating datetime as local time."""
        local_offset = timezone(timedelta(hours=self._get_timezone_offset()))
        local_dt = dt.replace(tzinfo=local_offset)
        utc_dt = local_dt.astimezone(timezone.utc)
        return int(utc_dt.timestamp())

    def _get_time_range(self) -> tuple[int, int]:
        """Get time range as timestamps to avoid Aliyun SDK timezone issues."""
        from_time = self._calculate_utc_timestamp(self.start_time)
        to_time = self._calculate_utc_timestamp(self.end_time)

        self.logger.info(f"Time range - start_time: {self.start_time} -> from_time: {from_time}")
        self.logger.info(f"Time range - end_time: {self.end_time} -> to_time: {to_time}")

        return from_time, to_time

    def handle_aliyun_error(self, error: Exception, retry_count: int, max_retries: int) -> int:
        """Handle Aliyun SLS specific errors with appropriate delays."""
        error_msg = str(error)

        # Handle specific Aliyun SLS error codes
        if "ReadQuotaExceed" in error_msg:
            self.logger.warning(
                f"Read quota exceeded (attempt {retry_count}/{max_retries}). Waiting 5 seconds before retry..."
            )
            time.sleep(5.0)  # Longer delay for quota issues
        elif "QpsLimitExceeded" in error_msg or "MetaOperationQpsLimitExceeded" in error_msg:
            self.logger.warning(
                f"QPS limit exceeded (attempt {retry_count}/{max_retries}). Waiting 3 seconds before retry..."
            )
            time.sleep(3.0)  # Medium delay for QPS issues
        elif "ServerBusy" in error_msg or "RequestTimeout" in error_msg:
            self.logger.warning(
                f"Server busy/timeout (attempt {retry_count}/{max_retries}). Waiting 2 seconds before retry..."
            )
            time.sleep(2.0)  # Short delay for server issues
        else:
            self.logger.warning(f"Error fetching logs (attempt {retry_count}/{max_retries}): {error}")
            time.sleep(1.0)  # Default delay

        return retry_count + 1

    def _process_logs_batch(self, logs, handlers):
        """Process a batch of logs and send to handlers."""
        for log in logs:
            raw_contents = log.get_contents()
            log_entry = self._process_log_contents(log, raw_contents)

            # Handle all handlers in one loop
            for h in handlers:
                h.handle(log_entry)

    def _create_logs_request(
        self, from_time: int, to_time: int, offset: int = 0, limit: int = DEFAULT_BATCH_SIZE
    ) -> "GetLogsRequest":
        """Create a GetLogsRequest with appropriate parameters."""
        has_pagination_in_query = self.is_sql_or_logsearch_query(self.query or "")

        if has_pagination_in_query:
            # For queries with pagination, we need to modify the query to include our offset/limit
            modified_query = self._add_pagination_to_query(self.query or "")

            return GetLogsRequest(
                self.project,
                self.logstore,
                from_time,
                to_time,
                query=modified_query,
                reverse=False,
            )
        else:
            # Use standard offset pagination
            return GetLogsRequest(
                self.project,
                self.logstore,
                from_time,
                to_time,
                query=self.query,
                line=limit,
                offset=offset,
                reverse=False,
            )

    def _add_pagination_to_query(self, query: str) -> str:
        """Add pagination parameters to existing query."""
        # Check if query already has limit clause
        if "limit" in query.lower():
            return query
        else:
            # Add limit and offset to query
            return f"{query} limit {0},{DEFAULT_BATCH_SIZE}"

    @with_retry()
    def _get_total_log_count(self) -> int:
        """Get total log count using histograms API."""
        from_time, to_time = self._get_time_range()

        # Check if query is an analysis statement (SQL or LogSearch analysis)
        if self.is_sql_or_logsearch_query(self.query or ""):
            self.logger.warning(
                f"Query '{self.query}' appears to be an analysis statement. "
                "Histograms API does not support analysis queries. "
                "Will use get_log_all method for fetching data."
            )
            # Return a large number to trigger get_log_all method
            return LARGE_DATASET_THRESHOLD + 1

        request = GetHistogramsRequest(self.project, self.logstore, from_time, to_time, query=self.query or "")

        response = self.client.get_histograms(request)
        total_logs = response.get_total_count()
        self.logger.info(f"Total logs to fetch: {total_logs}")
        return total_logs

    def _fetch_logs_batch(
        self, offset: int, limit: int, from_time: int, to_time: int
    ) -> Generator[Dict[str, Any], None, None]:
        """Fetch logs in a single batch using offset pagination."""
        request = self._create_logs_request(from_time, to_time, offset, limit)
        response = self.client.get_logs(request)

        if response:
            logs = response.get_logs()
            batch_logs = []
            for log in logs:
                raw_contents = log.get_contents()
                if not self.fields:
                    batch_logs.append(raw_contents)
                else:
                    batch_logs.append(self._process_log_contents(log, raw_contents))

            return batch_logs

    def _fetch_logs_with_get_log_all(self, handlers):
        """Fetch logs using get_log_all method for large datasets."""
        self.logger.info("Starting get_log_all fetch...")
        start_time = time.time()
        total_processed = 0
        batch_count = 0
        max_retries = 3
        retry_count = 0

        from_time, to_time = self._get_time_range()
        while True:
            try:
                for response in self.client.get_log_all(
                    self.project, self.logstore, from_time, to_time, query=self.query, reverse=False
                ):
                    if response:
                        logs = response.get_logs()
                        batch_count += 1
                        logs_count = len(logs)
                        total_processed += logs_count

                        # Log progress every 50 batches to reduce logging overhead
                        if batch_count % 50 == 0:
                            elapsed_time = time.time() - start_time
                            rate = total_processed / elapsed_time if elapsed_time > 0 else 0
                            self.logger.info(
                                f"Fetched {logs_count} logs from get_log_all (batch {batch_count}, total: {total_processed:,}, rate: {rate:.0f} logs/sec)"
                            )

                        # Process logs directly - optimize for speed
                        for log in logs:
                            raw_contents = log.get_contents()

                            # Skip field processing if no fields specified for maximum speed
                            if not self.fields:
                                log_entry = raw_contents
                            else:
                                log_entry = self._process_log_contents(log, raw_contents)

                            # Handle all handlers in one loop
                            for h in handlers:
                                h.handle(log_entry)

                # If we reach here, the generator completed successfully
                break

            except Exception as e:
                retry_count = self.handle_aliyun_error(e, retry_count, max_retries)
                if retry_count >= max_retries:
                    self.logger.error(f"Max retries reached for get_log_all, stopping: {e}")
                    raise e
                # Continue the loop to retry
                continue

        elapsed_time = time.time() - start_time
        final_rate = total_processed / elapsed_time if elapsed_time > 0 else 0
        self.logger.info(
            f"get_log_all fetch completed: {total_processed:,} logs in {elapsed_time:.1f}s ({final_rate:.0f} logs/sec)"
        )

    def _fetch_logs_with_pagination(self, handlers, total_logs):
        """Fetch logs using standard pagination method for smaller datasets."""
        batch_size = 1000
        self.logger.info(f"Using batch size: {batch_size}")

        # Fetch logs in batches using offset pagination
        offset = 0
        processed_count = 0
        from_time, to_time = self._get_time_range()

        while offset < total_logs:
            self.logger.info(
                f"Fetching logs batch: offset={offset:,}, limit={batch_size} (processed: {processed_count:,}/{total_logs:,})"
            )

            # Retry logic for each batch
            max_retries = 3
            retry_count = 0
            batch_success = False

            while retry_count < max_retries and not batch_success:
                try:
                    for log_entry in self._fetch_logs_batch(offset, batch_size, from_time, to_time):
                        for h in handlers:
                            h.handle(log_entry)
                        processed_count += 1

                    offset += batch_size
                    batch_success = True

                except Exception as e:
                    retry_count = self.handle_aliyun_error(e, retry_count, max_retries)
                    if retry_count >= max_retries:
                        self.logger.error(f"Failed to fetch batch at offset {offset}: {e}")
                        raise e
                    # Continue retry loop for the same batch
                    continue

    def execute_impl(self):
        handlers = self.create_handlers()
        self.logger.info("execute with context")
        self.logger.info(f"query: {self.query}")
        self.logger.info(f"start_time: {self.start_time}")
        self.logger.info(f"end_time: {self.end_time}")
        self.logger.info(f"fields: {self.fields}")

        # Get total log count using histograms
        total_logs = self._get_total_log_count()

        if total_logs == 0:
            self.logger.info("No logs found for the specified time range and query")
            return

        # Choose appropriate method based on log count
        if total_logs > LARGE_DATASET_THRESHOLD:  # More than 500k logs - use get_log_all for better performance
            self.logger.info(f"Large dataset detected ({total_logs:,} logs), using get_log_all method")
            self._fetch_logs_with_get_log_all(handlers)
        else:
            self.logger.info(f"Using standard pagination method for {total_logs:,} logs")
            self._fetch_logs_with_pagination(handlers, total_logs)

        for h in handlers:
            h.close()
        self.join_handlers()
