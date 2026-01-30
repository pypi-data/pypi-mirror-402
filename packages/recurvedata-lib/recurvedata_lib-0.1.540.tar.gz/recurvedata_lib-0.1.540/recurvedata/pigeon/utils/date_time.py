import datetime
from typing import List, Union

import dateutil.parser
import pendulum

_tz_utc = pendulum.timezone("utc")
_tz_local = pendulum.local_timezone()

_DATELIKE = Union[str, datetime.datetime, datetime.date, pendulum.DateTime, pendulum.Date]
_TZ_TYPE = Union[datetime.tzinfo, str]


def utcnow() -> datetime.datetime:
    """Current datetime in UTC timezone, naive format (without timezone info).
    e.g. datetime.datetime(2022, 10, 8, 9, 52, 13, 489857)
    """
    return datetime.datetime.utcnow()


def utcnow_aware() -> datetime.datetime:
    """Current datetime in UTC timezone, aware format (with timezone info).
    e.g. datetime.datetime(2022, 10, 8, 9, 52, 13, 489857, tzinfo=tzutc())
    """
    return datetime.datetime.utcnow().replace(tzinfo=_tz_utc)


def now() -> datetime.datetime:
    """Current datetime in local timezone, naive format (without timezone info).
    e.g. datetime.datetime(2022, 10, 8, 17, 52, 13, 489857)
    """
    return datetime.datetime.now()


def now_aware() -> datetime.datetime:
    """Current datetime in local timezone, naive format (with timezone info).
    e.g. datetime.datetime(2022, 10, 8, 17, 52, 13, 489857, tzinfo=tzlocal())
    """
    return datetime.datetime.now(tz=_tz_local)


def _ensure_datetime(dttm: _DATELIKE) -> datetime.datetime:
    """Convert a date-like value to a datetime.datetime object, leave the timezone info as-is

    >>> _ensure_datetime('2022-09-10')
    datetime.datetime(2022, 9, 10, 0, 0)
    >>> _ensure_datetime('2022-09-10 08:00:00+00:00')
    datetime.datetime(2022, 9, 10, 8, 0, tzinfo=tzutc())
    >>> _ensure_datetime(datetime.datetime(2022, 9, 10))
    datetime.datetime(2022, 9, 10, 0, 0)
    >>> _ensure_datetime(pendulum.parse('2022-09-10 08:00:00+00:00'))
    datetime.datetime(2022, 9, 10, 8, 0, tzinfo=Timezone('+00:00'))
    """
    if isinstance(dttm, pendulum.DateTime):
        return datetime.datetime.fromtimestamp(dttm.timestamp(), dttm.tz)
    if isinstance(dttm, datetime.datetime):
        return dttm
    if isinstance(dttm, datetime.date):
        return datetime.datetime.combine(dttm, datetime.time.min)
    if isinstance(dttm, str):
        return dateutil.parser.parse(dttm)
    raise TypeError(f"unsupported type {type(dttm)}")


def to_pendulum(dttm: _DATELIKE) -> pendulum.DateTime:
    """Convert a date-like value into pendulum.DateTime

    >>> to_pendulum('2022-09-10')
    DateTime(2022, 9, 10, 0, 0, 0, tzinfo=Timezone('UTC'))
    >>> to_pendulum('2022-09-10 12:12:12')
    DateTime(2022, 9, 10, 12, 12, 12, tzinfo=Timezone('UTC'))
    >>> to_pendulum('2022-09-10 12:12:12+08:00')
    DateTime(2022, 9, 10, 12, 12, 12, tzinfo=Timezone('+08:00'))
    >>> to_pendulum(datetime.datetime(2022, 9, 10))
    DateTime(2022, 9, 10, 0, 0, 0, tzinfo=Timezone('UTC'))
    """
    if isinstance(dttm, str):
        return pendulum.parse(dttm)
    return pendulum.instance(dttm)


def as_local_datetime(dt: _DATELIKE) -> datetime.datetime:
    """Convert a date-like value into local timezone, ignore the original timezone

    Note those tests only work well in timezon Asia/Shanghai
    >>> as_local_datetime('2022-09-10')
    datetime.datetime(2022, 9, 10, 0, 0, tzinfo=Timezone('Asia/Shanghai'))
    >>> as_local_datetime('2022-09-10 12:12:12+08:00')
    datetime.datetime(2022, 9, 10, 12, 12, 12, tzinfo=Timezone('Asia/Shanghai'))
    >>> as_local_datetime(pendulum.parse('2022-09-10 08:00:00+00:00'))
    datetime.datetime(2022, 9, 10, 8, 0, tzinfo=Timezone('Asia/Shanghai'))
    """
    return _ensure_datetime(dt).replace(tzinfo=_tz_local)


def _ensure_tz(tz_or_name: _TZ_TYPE) -> datetime.tzinfo:
    if isinstance(tz_or_name, str):
        return pendulum.timezone(tz_or_name)
    return tz_or_name


def convert_tz(dt: _DATELIKE, source: _TZ_TYPE, to: _TZ_TYPE) -> datetime.datetime:
    """Convert timezone.

    >>> convert_tz('2022-09-10 08:00:00', 'Asia/Shanghai', 'UTC')
    datetime.datetime(2022, 9, 10, 0, 0, tzinfo=Timezone('UTC'))
    >>> convert_tz('2022-09-10 00:00:00', 'UTC', 'Asia/Shanghai')
    datetime.datetime(2022, 9, 10, 8, 0, tzinfo=Timezone('Asia/Shanghai'))
    >>> convert_tz('2022-09-10 00:00:00', 'Europe/Paris', 'Asia/Shanghai')
    datetime.datetime(2022, 9, 10, 6, 0, tzinfo=Timezone('Asia/Shanghai'))
    """
    return _ensure_datetime(dt).replace(tzinfo=_ensure_tz(source)).astimezone(_ensure_tz(to))


def local_to_utc(dt: _DATELIKE) -> datetime.datetime:
    """Convert a datetime from local to utc

    >>> local_to_utc('2022-09-10 08:00:00')
    datetime.datetime(2022, 9, 10, 0, 0, tzinfo=Timezone('UTC'))
    >>> local_to_utc('2022-09-10 08:00:00+08:00')
    datetime.datetime(2022, 9, 10, 0, 0, tzinfo=Timezone('UTC'))
    """
    return convert_tz(dt, source=_tz_local, to=_tz_utc)


def utc_to_local(dt: _DATELIKE) -> datetime.datetime:
    """Convert a datetime from utc to local

    >>> utc_to_local('2022-09-10 08:00:00')
    datetime.datetime(2022, 9, 10, 16, 0, tzinfo=Timezone('Asia/Shanghai'))
    >>> utc_to_local('2022-09-10 08:00:00+00:00')
    datetime.datetime(2022, 9, 10, 16, 0, tzinfo=Timezone('Asia/Shanghai'))
    """
    return convert_tz(dt, source=_tz_utc, to=_tz_local)


def truncate_second(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "second")


def truncate_minute(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "minute")


def truncate_hour(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "hour")


def truncate_day(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "day")


def truncate_week(dttm: _DATELIKE) -> datetime.datetime:
    dttm = truncate(dttm, "day")
    return dttm - datetime.timedelta(days=dttm.isoweekday() - 1)


def truncate_month(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "month")


def truncate_half_month(dttm: _DATELIKE) -> datetime.datetime:
    dttm = truncate_day(dttm)
    if dttm.day >= 15:
        return dttm.replace(day=15)
    return dttm.replace(day=1)


def truncate_quarter(dttm: _DATELIKE) -> datetime.datetime:
    dttm = truncate(dttm, "month")

    month = dttm.month
    if 1 <= month <= 3:
        return dttm.replace(month=1)
    elif 4 <= month <= 6:
        return dttm.replace(month=4)
    elif 7 <= month <= 9:
        return dttm.replace(month=7)
    elif 10 <= month <= 12:
        return dttm.replace(month=10)


def truncate_half_year(dttm: _DATELIKE) -> datetime.datetime:
    dttm = truncate(dttm, "month")
    if 1 <= dttm.month <= 6:
        return dttm.replace(month=1)
    return dttm.replace(month=7)


def truncate_year(dttm: _DATELIKE) -> datetime.datetime:
    return truncate(dttm, "year")


_PERIODS = {
    "second": dict(microsecond=0),
    "minute": dict(microsecond=0, second=0),
    "hour": dict(microsecond=0, second=0, minute=0),
    "day": dict(
        microsecond=0,
        second=0,
        minute=0,
        hour=0,
    ),
    "month": dict(microsecond=0, second=0, minute=0, hour=0, day=1),
    "year": dict(microsecond=0, second=0, minute=0, hour=0, day=1, month=1),
}
_ODD_PERIODS = {"week": truncate_week, "quarter": truncate_quarter, "half_year": truncate_half_year}


def truncate(dttm: _DATELIKE, truncate_to="day") -> datetime.datetime:
    dttm = _ensure_datetime(dttm)
    if truncate_to in _PERIODS:
        return dttm.replace(**_PERIODS[truncate_to])

    if truncate_to not in _ODD_PERIODS:
        raise ValueError(
            "truncate_to not valid. Valid periods: {}".format(
                ", ".join(list(_PERIODS.keys()) + list(_ODD_PERIODS.keys()))
            )
        )
    return _ODD_PERIODS[truncate_to](dttm)


def date_add(dttm: _DATELIKE, days: int) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> date_add(dttm, 6)
    datetime.datetime(2022, 10, 14, 0, 0)
    >>> date_add('2022-10-08', 6)
    datetime.datetime(2022, 10, 14, 0, 0)
    """
    return _ensure_datetime(dttm) + datetime.timedelta(days=days)


def month_start(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> month_start(dttm)
    datetime.datetime(2022, 10, 1, 0, 0)
    """
    return truncate_month(dttm)


def month_end(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> month_end(dttm)
    datetime.datetime(2022, 10, 31, 0, 0)
    """
    dt = to_pendulum(dttm).last_of("month")
    return datetime.datetime(dt.year, dt.month, dt.day)


def _get_last_month(dttm: _DATELIKE) -> datetime.datetime:
    return month_start(dttm) - datetime.timedelta(days=1)


def last_month_start(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> last_month_start(dttm)
    datetime.datetime(2022, 9, 1, 0, 0)
    """
    return month_start(_get_last_month(dttm))


def last_month_end(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> last_month_end(dttm)
    datetime.datetime(2022, 9, 30, 0, 0)
    """
    return month_start(dttm) - datetime.timedelta(days=1)


def _get_last_week(dttm: _DATELIKE) -> datetime.datetime:
    return truncate_week(dttm) - datetime.timedelta(days=7)


def last_week_start(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> last_week_start(dttm)
    datetime.datetime(2022, 9, 26, 0, 0)
    """
    return truncate_week(dttm) - datetime.timedelta(days=7)


def last_week_end(dttm: _DATELIKE) -> datetime.datetime:
    """
    >>> dttm = datetime.datetime(2022, 10, 8)
    >>> last_week_end(dttm)
    datetime.datetime(2022, 10, 2, 0, 0)
    """
    return truncate_week(dttm) - datetime.timedelta(days=1)


def month_range(start_date: _DATELIKE, end_date: _DATELIKE) -> List[str]:
    """Get the first day of all months between start_date and end_date

    >>> month_range('2022-01-02', '2022-05-20')
    ['2022-01-01', '2022-02-01', '2022-03-01', '2022-04-01', '2022-05-01']
    """
    start_date = to_pendulum(start_date).replace(day=1)
    end_date = to_pendulum(end_date).replace(day=1)
    return [x.date().isoformat() for x in pendulum.period(start_date, end_date).range("months")]


def day_range(start_date: _DATELIKE, end_date: _DATELIKE) -> List[str]:
    """Get all dates between start_date and end_date

    >>> day_range('2022-01-02', '2022-01-07')
    ['2022-01-02', '2022-01-03', '2022-01-04', '2022-01-05', '2022-01-06', '2022-01-07']
    """
    start_date = to_pendulum(start_date)
    end_date = to_pendulum(end_date)
    return [x.date().isoformat() for x in pendulum.period(start_date, end_date).range("days")]


if __name__ == "__main__":
    import doctest

    doctest.testmod()
