from dataclasses import dataclass

from recurvedata.utils.crontab import next_schedule, previous_schedule
from recurvedata.utils.date_time import _DATELIKE


@dataclass
class DagBase:
    """
    Recurve Web Job 对象
    """

    id: int
    project_id: int
    name: str
    schedule_interval: str
    scheduler_type: str
    timezone: str
    owner: str
    full_refresh_models: bool = False
    retries: int = None
    retry_delay: int = None
    # for dbt operator
    skip_data_tests: bool = False

    @classmethod
    def normalize_schedule_interval(cls, interval: str) -> str:
        mapping = {
            "@once": None,
            "@hourly": "0 * * * *",
            "@daily": "0 0 * * *",
            "@weekly": "0 0 * * 0",
            "@monthly": "0 0 1 * *",
            "@yearly": "0 0 1 1 *",
        }
        if interval in mapping:
            return mapping[interval]
        return interval

    def next_schedule(self, dttm: _DATELIKE) -> _DATELIKE:
        return next_schedule(self.schedule_interval, dttm)

    def previous_schedule(self, dttm: _DATELIKE) -> _DATELIKE:
        return previous_schedule(self.schedule_interval, dttm)

    @property
    def is_once(self):
        return self.schedule_interval == "@once" or self.schedule_interval is None or self.schedule_interval == ""


@dataclass
class NodeBase:
    id: int
    node_key: str
    name: str
