"""Parse ISO 8601 timestamp strings."""

import datetime


def parse_iso8601_timestamp(timestamp_text):
    """Parse an ISO 8601 timestamp string into a timezone-aware datetime."""

    parsed = datetime.datetime.fromisoformat(timestamp_text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.timezone.utc)

    return parsed
