"""Write event records as individual JSON files grouped by local start year."""

import json
import logging
import os

import calendar_slicer.jsonl_writer
import calendar_slicer.timestamp_utility

_LOGGER = logging.getLogger(__name__)


def _sanitize_event_id_for_file_name(event_id):
    """Return a filesystem-safe basename stem for an event id."""

    sanitized = event_id.replace("/", "_").replace("\\", "_")

    return sanitized


def _build_binned_event_record(record, local_timezone):
    """Return a copy of record with start_timestamp in local_timezone."""

    local_start = calendar_slicer.timestamp_utility.convert_iso8601_timestamp_to_timezone(
        record["start_timestamp"],
        local_timezone,
    )
    binned_record = dict(record)
    binned_record["start_timestamp"] = local_start.isoformat()

    return binned_record, local_start


def write_events(records, output_bin_path, jsonl_output_stream=None, local_timezone=None):
    """Write each event under output_bin_path/<local-start-year>/<event_id>.json."""

    if local_timezone is None:
        local_timezone = calendar_slicer.timestamp_utility.get_local_timezone()

    output_bin_root = os.path.abspath(output_bin_path)
    os.makedirs(output_bin_root, exist_ok=True)

    # Emit JSONL and binned JSON files in one pass over the record stream.
    for record in records:
        if jsonl_output_stream is not None:
            calendar_slicer.jsonl_writer.write_jsonl_record(record, jsonl_output_stream)

        binned_record, local_start = _build_binned_event_record(record, local_timezone)
        year_directory_name = str(local_start.year)
        year_directory_path = os.path.join(output_bin_root, year_directory_name)
        os.makedirs(year_directory_path, exist_ok=True)

        event_file_name = "{event_id}.json".format(
            event_id=_sanitize_event_id_for_file_name(record["event_id"]),
        )
        event_file_path = os.path.join(year_directory_path, event_file_name)

        # Skip binned files that already exist at the target path.
        if os.path.isfile(event_file_path):

            continue

        with open(event_file_path, "w", encoding="utf-8") as output_stream:
            json.dump(binned_record, output_stream, ensure_ascii=False)
            output_stream.write("\n")
