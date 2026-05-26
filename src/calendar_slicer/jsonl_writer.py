"""Write event records as JSON Lines."""

import json
import logging

_LOGGER = logging.getLogger(__name__)


def write_jsonl_record(record, output_stream):
    """Write one record dictionary as a JSON line to output_stream."""

    json_line = json.dumps(record, ensure_ascii=False)
    output_stream.write(json_line)
    output_stream.write("\n")


def write_jsonl(records, output_stream):
    """Write each record dictionary as one JSON line to output_stream."""

    # Serialize each record as a single JSONL row.
    for record in records:
        write_jsonl_record(record, output_stream)
