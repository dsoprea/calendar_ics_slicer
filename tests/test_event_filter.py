"""Tests for event record time filtering."""

import datetime

import calendar_slicer.event_filter

SAMPLE_RECORDS = [
    {
        "name": "Old Event",
        "calendar": "Test",
        "start_timestamp": "2020-01-01T00:00:00+00:00",
        "stop_timestamp": "2020-01-01T01:00:00+00:00",
    },
    {
        "name": "Middle Event",
        "calendar": "Test",
        "start_timestamp": "2025-03-01T00:00:00+00:00",
        "stop_timestamp": "2025-03-01T01:00:00+00:00",
    },
    {
        "name": "Future Event",
        "calendar": "Test",
        "start_timestamp": "2026-06-01T00:00:00+00:00",
        "stop_timestamp": "2026-06-01T01:00:00+00:00",
    },
]


def test_iter_matching_event_records_applies_earliest_and_latest_bounds():
    """Records outside the start timestamp window are omitted."""

    filtered = list(calendar_slicer.event_filter.iter_matching_event_records(
        SAMPLE_RECORDS,
        earliest_inclusive=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
        latest_inclusive=datetime.datetime(2025, 12, 31, tzinfo=datetime.timezone.utc),
    ))

    assert [record["name"] for record in filtered] == ["Middle Event"]


def test_build_event_time_bounds_applies_maximum_age_cutoff():
    """Maximum age sets a rolling earliest bound from the reference instant."""

    reference_instant = datetime.datetime(2025, 6, 1, tzinfo=datetime.timezone.utc)
    earliest_inclusive, latest_inclusive = calendar_slicer.event_filter.build_event_time_bounds(
        maximum_age_phrase="10 weeks",
        reference_instant=reference_instant,
    )

    assert latest_inclusive is None
    assert earliest_inclusive == datetime.datetime(2025, 3, 23, tzinfo=datetime.timezone.utc)


def test_build_event_time_bounds_uses_later_of_maximum_age_and_earliest_timestamp():
    """Explicit earliest timestamps combine with maximum age using the later cutoff."""

    reference_instant = datetime.datetime(2025, 6, 1, tzinfo=datetime.timezone.utc)
    earliest_inclusive, latest_inclusive = calendar_slicer.event_filter.build_event_time_bounds(
        maximum_age_phrase="10 weeks",
        earliest_timestamp_text="2025-05-01T00:00:00+00:00",
        reference_instant=reference_instant,
    )

    assert earliest_inclusive == datetime.datetime(2025, 5, 1, tzinfo=datetime.timezone.utc)
