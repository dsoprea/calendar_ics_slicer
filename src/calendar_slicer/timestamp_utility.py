"""Parse ISO 8601 timestamp strings."""

import datetime


def parse_iso8601_timestamp(timestamp_text):
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime."""

    parsed = datetime.datetime.fromisoformat(timestamp_text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)

    return parsed


def get_local_timezone():
    """Return the system local timezone."""

    return datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


def convert_iso8601_timestamp_to_timezone(timestamp_text, target_timezone):
    """Parse timestamp_text and return it in target_timezone."""

    parsed = parse_iso8601_timestamp(timestamp_text)
    converted = parsed.astimezone(target_timezone)

    return converted
