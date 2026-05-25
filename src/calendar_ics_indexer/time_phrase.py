"""Parse human-readable time interval phrases such as ``10 weeks``."""

import datetime
import re

import dateutil.relativedelta

_RELATIVE_DELTA_UNITS = {
    "month": "months",
    "months": "months",
    "mo": "months",
    "year": "years",
    "years": "years",
    "yr": "years",
    "y": "years",
}

_TIMEDELTA_UNITS = {
    "second": "seconds",
    "seconds": "seconds",
    "sec": "seconds",
    "s": "seconds",
    "minute": "minutes",
    "minutes": "minutes",
    "min": "minutes",
    "m": "minutes",
    "hour": "hours",
    "hours": "hours",
    "hr": "hours",
    "h": "hours",
    "day": "days",
    "days": "days",
    "d": "days",
    "week": "weeks",
    "weeks": "weeks",
    "wk": "weeks",
    "w": "weeks",
}

_TIME_PHRASE_PATTERN = re.compile(
    r"^\s*(?P<count>\d+)\s+(?P<unit>[a-zA-Z]+)\s*$",
)


def parse_time_phrase(phrase):
    """Parse a count-and-unit phrase into a timedelta or relativedelta."""

    match = _TIME_PHRASE_PATTERN.match(phrase)
    if match is None:
        message = "unsupported time phrase: {phrase}".format(phrase=phrase)
        raise ValueError(message)

    count_text = match.group("count")
    unit_text = match.group("unit").lower()
    count = int(count_text)

    if unit_text in _RELATIVE_DELTA_UNITS:
        relative_delta_keyword = _RELATIVE_DELTA_UNITS[unit_text]
        delta_kwargs = {relative_delta_keyword: count}

        return dateutil.relativedelta.relativedelta(**delta_kwargs)

    if unit_text in _TIMEDELTA_UNITS:
        timedelta_keyword = _TIMEDELTA_UNITS[unit_text]
        delta_kwargs = {timedelta_keyword: count}

        return datetime.timedelta(**delta_kwargs)

    message = "unsupported time unit in phrase: {phrase}".format(phrase=phrase)
    raise ValueError(message)


def subtract_time_phrase(instant, phrase):
    """Return instant minus the interval described by phrase."""

    interval = parse_time_phrase(phrase)

    if isinstance(interval, datetime.timedelta):
        return instant - interval

    return instant - interval
