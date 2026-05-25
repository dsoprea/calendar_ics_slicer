"""Tests for time interval phrase parsing."""

import datetime

import calendar_slicer.time_phrase


def test_parse_time_phrase_supports_weeks():
    """Week phrases parse into timedeltas."""

    interval = calendar_slicer.time_phrase.parse_time_phrase("10 weeks")

    assert interval == datetime.timedelta(weeks=10)


def test_subtract_time_phrase_moves_instant_backward():
    """Subtracting a phrase returns an earlier instant."""

    reference_instant = datetime.datetime(2025, 6, 1, 12, 0, tzinfo=datetime.timezone.utc)
    cutoff_instant = calendar_slicer.time_phrase.subtract_time_phrase(
        reference_instant,
        "2 days",
    )

    assert cutoff_instant == datetime.datetime(2025, 5, 30, 12, 0, tzinfo=datetime.timezone.utc)


def test_parse_time_phrase_rejects_unknown_unit():
    """Unknown units raise ValueError."""

    try:
        calendar_slicer.time_phrase.parse_time_phrase("3 fortnights")
        raised = False
    except ValueError:
        raised = True

    assert raised
