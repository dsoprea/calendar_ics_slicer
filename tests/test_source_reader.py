"""Tests for reading ICS sources from files and ZIP archives."""

import io
import os
import tempfile
import zipfile

import calendar_slicer.source_reader

SAMPLE_ICS = """\
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//EN
X-WR-CALNAME:Embedded Calendar
BEGIN:VEVENT
UID:zip-event-1
SUMMARY:Zip Meeting
DTSTART:20250410T090000Z
DTEND:20250410T100000Z
END:VEVENT
END:VCALENDAR
"""


def test_iter_event_records_reads_single_ics_file():
    """A standalone ICS file yields its events."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        ics_path = os.path.join(temporary_directory, "standalone.ics")
        with open(ics_path, "w", encoding="utf-8") as output_stream:
            output_stream.write(SAMPLE_ICS)

        records = list(calendar_slicer.source_reader.iter_event_records(ics_path))

    assert len(records) == 1
    assert records[0]["name"] == "Zip Meeting"
    assert records[0]["calendar"] == "Embedded Calendar"


def test_iter_event_records_reads_ics_files_inside_zip():
    """ZIP archives yield events from nested .ics members."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        zip_path = os.path.join(temporary_directory, "calendars.zip")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("School/events.ics", SAMPLE_ICS)
            archive.writestr("Work/planning.ics", SAMPLE_ICS)

        with open(zip_path, "wb") as output_stream:
            output_stream.write(buffer.getvalue())

        records = list(calendar_slicer.source_reader.iter_event_records(zip_path))

    assert len(records) == 2
    assert records[0]["name"] == "Zip Meeting"
    assert records[0]["calendar"] == "Embedded Calendar"


def test_count_ics_source_files_counts_zip_members():
    """ZIP archives report one source per .ics member."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        zip_path = os.path.join(temporary_directory, "calendars.zip")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("School/events.ics", SAMPLE_ICS)
            archive.writestr("Work/planning.ics", SAMPLE_ICS)
            archive.writestr("Work/readme.txt", "ignore me")

        with open(zip_path, "wb") as output_stream:
            output_stream.write(buffer.getvalue())

        source_file_count = calendar_slicer.source_reader.count_ics_source_files(zip_path)

    assert source_file_count == 2


def test_count_ics_source_files_counts_single_ics_file():
    """A standalone ICS path counts as one source file."""

    with tempfile.TemporaryDirectory() as temporary_directory:
        ics_path = os.path.join(temporary_directory, "standalone.ics")
        with open(ics_path, "w", encoding="utf-8") as output_stream:
            output_stream.write(SAMPLE_ICS)

        source_file_count = calendar_slicer.source_reader.count_ics_source_files(ics_path)

    assert source_file_count == 1


def test_iter_event_records_invokes_source_progress_callback_per_file():
    """Each ICS source triggers one progress callback."""

    progress_updates = []

    with tempfile.TemporaryDirectory() as temporary_directory:
        zip_path = os.path.join(temporary_directory, "calendars.zip")
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("School/events.ics", SAMPLE_ICS)
            archive.writestr("Work/planning.ics", SAMPLE_ICS)

        with open(zip_path, "wb") as output_stream:
            output_stream.write(buffer.getvalue())

        records = list(calendar_slicer.source_reader.iter_event_records(
            zip_path,
            source_progress_callback=progress_updates.append,
        ))

    assert len(records) == 2
    assert len(progress_updates) == 2
