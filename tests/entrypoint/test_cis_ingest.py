"""Tests for the cis_ingest CLI entrypoint."""

import datetime
import io
import json
import os
import tempfile
import unittest.mock
import zipfile

import calendar_slicer.entrypoint.cis_ingest

SAMPLE_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
X-WR-CALNAME:CLI Calendar
BEGIN:VEVENT
UID:cli-event-old
SUMMARY:Old CLI Event
DTSTART:20200101T120000Z
DTEND:20200101T130000Z
END:VEVENT
BEGIN:VEVENT
UID:cli-event-1
SUMMARY:CLI Event
DTSTART:20250601T120000Z
DTEND:20250601T130000Z
END:VEVENT
END:VCALENDAR
"""


def test_main_writes_jsonl_to_output_file():
    """The CLI writes one JSON object per line to the output file."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        ics_path = os.path.join(temporary_directory, "events.ics")
        output_path = os.path.join(temporary_directory, "events.jsonl")

        with open(ics_path, "w", encoding="utf-8") as output_stream:
            output_stream.write(SAMPLE_ICS)

        calendar_slicer.entrypoint.cis_ingest.main([
            ics_path,
            "--output",
            output_path,
        ])

        with open(output_path, "r", encoding="utf-8") as input_stream:
            lines = input_stream.readlines()

    assert len(lines) == 2
    record = json.loads(lines[1])
    assert record["event_id"] == "cli-event-1"
    assert record["name"] == "CLI Event"
    assert record["calendar"] == "CLI Calendar"
    assert record["start_timestamp"] == "2025-06-01T12:00:00+00:00"
    assert record["stop_timestamp"] == "2025-06-01T13:00:00+00:00"


def test_main_reads_zip_archive():
    """The CLI ingests .ics members from a ZIP archive."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        zip_path = os.path.join(temporary_directory, "bundle.zip")
        output_path = os.path.join(temporary_directory, "bundle.jsonl")
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("Family/holidays.ics", SAMPLE_ICS)

        with open(zip_path, "wb") as output_stream:
            output_stream.write(buffer.getvalue())

        calendar_slicer.entrypoint.cis_ingest.main([
            zip_path,
            "--output",
            output_path,
        ])

        with open(output_path, "r", encoding="utf-8") as input_stream:
            lines = input_stream.readlines()

    assert len(lines) == 2
    record = json.loads(lines[1])
    assert record["event_id"] == "cli-event-1"
    assert record["name"] == "CLI Event"


def test_main_filters_events_by_earliest_timestamp():
    """The CLI omits events before --earliest-timestamp."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        ics_path = os.path.join(temporary_directory, "events.ics")
        output_path = os.path.join(temporary_directory, "events.jsonl")

        with open(ics_path, "w", encoding="utf-8") as output_stream:
            output_stream.write(SAMPLE_ICS)

        calendar_slicer.entrypoint.cis_ingest.main([
            ics_path,
            "--output",
            output_path,
            "--earliest-timestamp",
            "2025-01-01T00:00:00+00:00",
        ])

        with open(output_path, "r", encoding="utf-8") as input_stream:
            lines = input_stream.readlines()

    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["event_id"] == "cli-event-1"
    assert record["name"] == "CLI Event"


def test_main_writes_binned_event_files_under_output_bin_path():
    """The CLI writes per-event JSON files grouped by local start year."""

    eastern = datetime.timezone(datetime.timedelta(hours=-5))

    with unittest.mock.patch(
        "calendar_slicer.timestamp_utility.get_local_timezone",
        return_value=eastern,
    ):
        with tempfile.TemporaryDirectory() as temporary_directory:
            ics_path = os.path.join(temporary_directory, "events.ics")
            output_path = os.path.join(temporary_directory, "events.jsonl")
            output_bin_path = os.path.join(temporary_directory, "bins")

            with open(ics_path, "w", encoding="utf-8") as output_stream:
                output_stream.write(SAMPLE_ICS)

            calendar_slicer.entrypoint.cis_ingest.main([
                ics_path,
                "--output",
                output_path,
                "--output-bin-path",
                output_bin_path,
            ])

            binned_event_path = os.path.join(output_bin_path, "2025", "cli-event-1.json")

            with open(binned_event_path, "r", encoding="utf-8") as input_stream:
                binned_record = json.load(input_stream)

            with open(output_path, "r", encoding="utf-8") as input_stream:
                jsonl_lines = input_stream.readlines()

    assert binned_record["event_id"] == "cli-event-1"
    assert binned_record["start_timestamp"] == "2025-06-01T07:00:00-05:00"
    assert len(jsonl_lines) == 2
    assert json.loads(jsonl_lines[1])["start_timestamp"] == "2025-06-01T12:00:00+00:00"
