"""Tests for ICS parsing."""

import logging

import calendar_slicer.ics_parser

SAMPLE_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
X-WR-CALNAME:Work Calendar
BEGIN:VEVENT
UID:event-1
SUMMARY:Team Standup
DTSTART:20250115T100000Z
DTEND:20250115T103000Z
END:VEVENT
BEGIN:VEVENT
UID:event-2
SUMMARY:All Day Offsite
DTSTART;VALUE=DATE:20250201
END:VEVENT
END:VCALENDAR
"""


def test_parse_ics_bytes_uses_calendar_property_and_event_fields():
    """Parsed records expose event id, name, calendar, and ISO 8601 timestamps."""

    records = list(calendar_slicer.ics_parser.parse_ics_bytes(
        SAMPLE_ICS.encode("utf-8"),
        "",
        "ignored.ics",
    ))

    assert len(records) == 2

    standup = records[0]
    assert standup["event_id"] == "event-1"
    assert standup["name"] == "Team Standup"
    assert standup["calendar"] == "Work Calendar"
    assert standup["start_timestamp"] == "2025-01-15T10:00:00+00:00"
    assert standup["stop_timestamp"] == "2025-01-15T10:30:00+00:00"

    all_day = records[1]
    assert all_day["event_id"] == "event-2"
    assert all_day["name"] == "All Day Offsite"
    assert all_day["start_timestamp"] == "2025-02-01T00:00:00+00:00"
    assert all_day["stop_timestamp"] == "2025-02-02T00:00:00+00:00"


def test_parse_ics_bytes_uses_folder_name_when_calendar_property_missing():
    """Folder name becomes the calendar when ICS metadata lacks a calendar name."""

    ics_without_calendar_name = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
BEGIN:VEVENT
UID:event-3
SUMMARY:Planning
DTSTART:20250301T140000Z
DTEND:20250301T150000Z
END:VEVENT
END:VCALENDAR
"""

    records = list(calendar_slicer.ics_parser.parse_ics_bytes(
        ics_without_calendar_name.encode("utf-8"),
        "Personal",
        "events.ics",
    ))

    assert records[0]["event_id"] == "event-3"
    assert records[0]["calendar"] == "Personal"


def test_parse_ics_bytes_skips_event_without_uid(caplog):
    """Events without a UID are logged and omitted from output."""

    ics_without_uid = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
X-WR-CALNAME:Work Calendar
BEGIN:VEVENT
SUMMARY:Missing UID Event
DTSTART:20250116T100000Z
DTEND:20250116T103000Z
END:VEVENT
BEGIN:VEVENT
UID:valid-event
SUMMARY:Valid Event
DTSTART:20250117T100000Z
DTEND:20250117T103000Z
END:VEVENT
END:VCALENDAR
"""

    with caplog.at_level(logging.ERROR, logger="calendar_slicer.ics_parser"):
        records = list(calendar_slicer.ics_parser.parse_ics_bytes(
            ics_without_uid.encode("utf-8"),
            "",
            "ignored.ics",
        ))

    assert len(records) == 1
    assert records[0]["event_id"] == "valid-event"
    assert "skipping event without UID" in caplog.text
