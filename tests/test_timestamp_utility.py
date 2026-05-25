"""Tests for ISO 8601 timestamp parsing."""

import datetime

import calendar_slicer.timestamp_utility


def test_parse_iso8601_timestamp_parses_utc_datetime():
    """UTC datetimes parse with timezone attached."""

    parsed = calendar_slicer.timestamp_utility.parse_iso8601_timestamp(
        "2025-06-01T12:00:00+00:00",
    )

    assert parsed == datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc)


def test_parse_iso8601_timestamp_assigns_utc_to_naive_values():
    """Naive timestamps are treated as UTC."""

    parsed = calendar_slicer.timestamp_utility.parse_iso8601_timestamp(
        "2025-06-01T12:00:00",
    )

    assert parsed == datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc)
