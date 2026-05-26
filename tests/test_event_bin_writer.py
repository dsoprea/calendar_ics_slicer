"""Tests for binned per-event JSON output."""

import datetime
import json
import os
import tempfile

import calendar_slicer.event_bin_writer


def test_write_events_groups_by_local_start_year():
    """Events are written under year directories using local start timestamps."""

    eastern = datetime.timezone(datetime.timedelta(hours=-5))
    records = [
        {
            "event_id": "event-a",
            "name": "New Years Eve",
            "calendar": "Work",
            "start_timestamp": "2025-01-01T04:00:00+00:00",
            "stop_timestamp": "2025-01-01T05:00:00+00:00",
        },
        {
            "event_id": "event-b",
            "name": "Summer Meeting",
            "calendar": "Work",
            "start_timestamp": "2025-06-01T12:00:00+00:00",
            "stop_timestamp": "2025-06-01T13:00:00+00:00",
        },
    ]

    with tempfile.TemporaryDirectory() as temporary_directory:
        calendar_slicer.event_bin_writer.write_events(
            records,
            temporary_directory,
            local_timezone=eastern,
        )

        event_a_path = os.path.join(temporary_directory, "2024", "event-a.json")
        event_b_path = os.path.join(temporary_directory, "2025", "event-b.json")

        assert os.path.isfile(event_a_path)
        assert os.path.isfile(event_b_path)

        with open(event_a_path, "r", encoding="utf-8") as input_stream:
            event_a_record = json.load(input_stream)

        with open(event_b_path, "r", encoding="utf-8") as input_stream:
            event_b_record = json.load(input_stream)

    assert event_a_record["start_timestamp"] == "2024-12-31T23:00:00-05:00"
    assert event_b_record["start_timestamp"] == "2025-06-01T07:00:00-05:00"


def test_write_events_sanitizes_path_separators_in_event_id():
    """Path separators in event ids are replaced before writing files."""

    eastern = datetime.timezone(datetime.timedelta(hours=-5))
    records = [
        {
            "event_id": "calendar/event-1",
            "name": "Nested UID",
            "calendar": "Work",
            "start_timestamp": "2025-06-01T12:00:00+00:00",
            "stop_timestamp": "2025-06-01T13:00:00+00:00",
        },
    ]

    with tempfile.TemporaryDirectory() as temporary_directory:
        calendar_slicer.event_bin_writer.write_events(
            records,
            temporary_directory,
            local_timezone=eastern,
        )

        event_path = os.path.join(temporary_directory, "2025", "calendar_event-1.json")

        assert os.path.isfile(event_path)


def test_write_events_also_writes_jsonl_when_stream_given():
    """Binned output can mirror records to a JSONL stream in the same pass."""

    eastern = datetime.timezone(datetime.timedelta(hours=-5))
    records = [
        {
            "event_id": "event-a",
            "name": "Summer Meeting",
            "calendar": "Work",
            "start_timestamp": "2025-06-01T12:00:00+00:00",
            "stop_timestamp": "2025-06-01T13:00:00+00:00",
        },
    ]

    with tempfile.TemporaryDirectory() as temporary_directory:
        jsonl_path = os.path.join(temporary_directory, "events.jsonl")

        with open(jsonl_path, "w", encoding="utf-8") as jsonl_output_stream:
            calendar_slicer.event_bin_writer.write_events(
                records,
                os.path.join(temporary_directory, "bins"),
                jsonl_output_stream=jsonl_output_stream,
                local_timezone=eastern,
            )

        with open(jsonl_path, "r", encoding="utf-8") as input_stream:
            jsonl_lines = input_stream.readlines()

    assert len(jsonl_lines) == 1
    jsonl_record = json.loads(jsonl_lines[0])
    assert jsonl_record["start_timestamp"] == "2025-06-01T12:00:00+00:00"


def test_write_events_skips_existing_event_file():
    """An existing binned event file at the target path is left unchanged."""

    eastern = datetime.timezone(datetime.timedelta(hours=-5))
    original_record = {
        "event_id": "event-a",
        "name": "Original Name",
        "calendar": "Work",
        "start_timestamp": "2025-06-01T12:00:00+00:00",
        "stop_timestamp": "2025-06-01T13:00:00+00:00",
    }
    updated_record = dict(original_record)
    updated_record["name"] = "Updated Name"

    with tempfile.TemporaryDirectory() as temporary_directory:
        calendar_slicer.event_bin_writer.write_events(
            [original_record],
            temporary_directory,
            local_timezone=eastern,
        )

        event_path = os.path.join(temporary_directory, "2025", "event-a.json")

        calendar_slicer.event_bin_writer.write_events(
            [updated_record],
            temporary_directory,
            local_timezone=eastern,
        )

        with open(event_path, "r", encoding="utf-8") as input_stream:
            stored_record = json.load(input_stream)

    assert stored_record["name"] == "Original Name"
