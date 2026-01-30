import logging
import sys
import threading
import traceback
from queue import Empty, Queue
from typing import Optional, Protocol, Type

from recurvedata.utils.log import AwareFormatter


class MessageHandler(Protocol):
    def __call__(self, message: str) -> None:
        ...


class OutputInterceptor:
    def __init__(self, handler: MessageHandler, flush_interval_seconds: int = 5, batch_size: int = 10) -> None:
        """
        Initialize the OutputInterceptor object.

        Args:
            handler: The handler to call with processed messages.
            flush_interval_seconds: Time interval (in seconds) between flushes.
            batch_size: Number of messages to accumulate before triggering a flush.
        """
        self.handler = handler
        self.flush_interval_seconds = flush_interval_seconds
        self.batch_size = batch_size

        self.queue: Queue[str] = Queue()
        self._stop_event = threading.Event()
        self._flusher_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self._flusher_thread.start()

        # Create a dedicated logger for internal use
        self._logger = logging.getLogger(self.logger_name)

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    @property
    def logger_name(self) -> str:
        return f"{__name__}.{self.__class__.__name__}"

    def __enter__(self) -> "OutputInterceptor":
        """Support for context management, starts the interceptor."""
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        exc_traceback: Optional[BaseException],
    ) -> None:
        """Ensure all remaining data is flushed when the context exits."""
        if exc_type is not None:
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
            self._write("".join(tb_lines))

        self.stop()

        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

    def write(self, s: str) -> None:
        """
        Write a string to the queue. This method is called when sys.stdout or sys.stderr is written to.
        """
        # Write to the original output stream
        if sys.stdout is self:
            self._original_stdout.write(s)
        elif sys.stderr is self:
            self._original_stderr.write(s)

        self._write(s)

    def flush(self) -> None:
        """No-op flush method to maintain compatibility with sys.stdout and sys.stderr."""
        pass

    def write_log(self, s: str) -> None:
        self._write(s + "\n")

    def _write(self, s: str) -> None:
        if isinstance(s, bytes):
            # when an error raised, the last line of s could be bytes
            s = s.decode("utf-8", errors="replace")
        # if s.strip():  # Ignore empty lines
        #     self.queue.put(s)
        self.queue.put(s)

        if self.queue.qsize() >= self.batch_size:
            self.flush_messages()
        elif self._stop_event.is_set():
            # when Exception, because we Propagate the exception, the exception will write to stderr after __exit__
            self.flush_messages()

    def _periodic_flush(self) -> None:
        """Periodically flush the queue and process each message using the processor."""
        while not self._stop_event.is_set():
            try:
                self.flush_messages()
            except Exception as e:
                self._logger.error(f"Error during message flush: {e}", exc_info=True)
            self._stop_event.wait(self.flush_interval_seconds)

    def flush_messages(self) -> None:
        """Flush all queued messages using the provided processor."""
        messages = []
        while True:
            try:
                messages.append(self.queue.get_nowait())
            except Empty:
                break
        if messages:
            try:
                self.handler("".join(messages))
            except Exception as e:
                self._logger.error(f"Failed to process messages: {e}", exc_info=True)

    def stop(self) -> None:
        """Stop the periodic flush thread and ensure any remaining data is processed."""
        self._stop_event.set()
        self._flusher_thread.join()
        self.flush_messages()  # Ensure all remaining data is processed


class LoggingHandler(logging.Handler):
    def __init__(self, interceptor: OutputInterceptor) -> None:
        super().__init__()
        self.interceptor = interceptor

    def emit(self, record: logging.LogRecord) -> None:
        # Filter out logs from the OutputInterceptor's own logger
        if record.name == self.interceptor.logger_name:
            return

        log_entry = self.format(record)
        self.interceptor.write_log(log_entry)


def setup_log_handler(
    interceptor: OutputInterceptor,
    fmt="[%(asctime)s] - %(levelname)s - %(name)s - %(filename)s:%(lineno)d - [%(process)d:%(threadName)s] - %(message)s",
    formatter_cls: Type[logging.Formatter] = AwareFormatter,
):
    handler = LoggingHandler(interceptor)
    handler.setFormatter(formatter_cls(fmt))
    logging.getLogger().addHandler(handler)
