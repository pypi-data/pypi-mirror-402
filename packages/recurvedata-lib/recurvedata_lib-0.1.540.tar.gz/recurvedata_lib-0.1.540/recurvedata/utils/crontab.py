import datetime
from typing import Optional

import croniter

from recurvedata.utils.date_time import DATELIKE


def normalize_schedule_interval(schedule_interval: str) -> str:
    mapping = {
        "@once": None,
        "@hourly": "0 * * * *",
        "@daily": "0 0 * * *",
        "@weekly": "0 0 * * 0",
        "@monthly": "0 0 1 * *",
        "@yearly": "0 0 1 1 *",
    }
    return mapping.get(schedule_interval, schedule_interval)


def _get_schedule(schedule_interval: str, dttm: DATELIKE, is_next: bool = False) -> Optional[DATELIKE]:
    cron_spec = normalize_schedule_interval(schedule_interval)
    if not cron_spec:
        return None
    start_time = dttm
    cron = croniter.croniter(cron_spec, start_time)
    if is_next:
        value = cron.get_next(datetime.datetime)
    else:
        value = cron.get_prev(datetime.datetime)
    return value


def next_schedule(schedule_interval: str, dttm: DATELIKE) -> DATELIKE:
    return _get_schedule(schedule_interval, dttm, is_next=True)


def previous_schedule(schedule_interval: str, dttm: DATELIKE) -> DATELIKE:
    return _get_schedule(schedule_interval, dttm, is_next=False)


get_schedule = _get_schedule
