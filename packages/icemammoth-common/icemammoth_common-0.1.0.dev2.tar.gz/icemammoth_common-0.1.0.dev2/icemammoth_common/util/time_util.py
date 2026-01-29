# -*- coding: utf-8 -*-

import time
from datetime import date, timedelta, datetime, timezone


DEFAULT_DATE_TIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_start_end_duration(dt="2021-05-05"):
    """[get (time - 2h, time + 27h)]

    Args:
        dt (str, optional): [description]. Defaults to "2021-05-05".

    Returns:
        [tuple(int)]
    """
    dt = date.fromisoformat(dt)
    tmr_dt = dt + timedelta(days=1)
    return int(time.mktime(date.timetuple(dt))),  int(time.mktime(date.timetuple(tmr_dt)) + 3 * 3600)


def get_short_start_end_duration(dt):
    """[get (time, time + 3h)]

    Returns:
        [tuple(int)]
    """
    dt = date.fromisoformat(dt)
    return int(time.mktime(date.timetuple(dt))),  int(time.mktime(date.timetuple(dt)) + 3 * 3600)


def get_now_time():
    return datetime.now().isoformat().split(".")[0]


def set2string(s):
    """[transform set to string]

    Args:
        s ([set])

    Returns:
        [string]
    """
    result = ''
    for i, k in enumerate(s):
        if i > 0:
            result += '\n'
        result += k
    return result


def get_current_unix_timestamp():
    return int(time.time())


def datetime_to_str(date_time: datetime, format=DEFAULT_DATE_TIME_FORMAT) -> str:
    if date_time is None:
        return None
    return date_time.strftime(format)


def str_to_datetime(date_time_str, format=DEFAULT_DATE_TIME_FORMAT) -> datetime:
    if date_time_str is None:
        return None
    return datetime.strptime(date_time_str, format)


def convert_unixtime_to_datetime(unixtimestmap) -> datetime:
    tz = timezone(timedelta(0, 28800))
    return datetime.fromtimestamp(unixtimestmap, tz=tz)


def datetime_add(time, days: int = 0, seconds: int = 0, microseconds: int = 0, milliseconds: int = 0, minutes: int = 0, hours: int = 0, weeks: int = 0) -> datetime:
    return time + timedelta(days, seconds, microseconds, milliseconds, minutes, hours, weeks)


def str_datetime_add(timeStr: str, days: int = 0, seconds: int = 0, microseconds: int = 0, milliseconds: int = 0, minutes: int = 0, hours: int = 0, weeks: int = 0, format: str = DEFAULT_DATE_TIME_FORMAT) -> str:
    time = datetime.strptime(timeStr, format)
    time: datetime = datetime_add(time=time, days=days, seconds=seconds, microseconds=microseconds,
                                  milliseconds=milliseconds, minutes=minutes, hours=hours, weeks=weeks)
    return time.strftime(format)


def get_week(time: datetime) -> int:

    if time is None:
        return None

     # 计算周一是一年中的第几天
    monday: datetime = time - timedelta(days=time.weekday())

    # 计算当前是今年的第几周
    # ISO 8601标准，周一是一周的开始
    return monday.isocalendar()[1]


def get_week_begin_date(time: datetime) -> str:

    if time is None:
        return None

    # 计算周一是一年中的第几天
    monday: datetime = time - timedelta(days=time.weekday())

    # 格式化周起始日期
    return monday.strftime('%Y-%m-%d')
