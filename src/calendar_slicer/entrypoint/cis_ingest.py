"""CLI entrypoint to ingest ICS files or ZIP archives and emit JSONL."""

import argparse
import logging
import os
import sys
import zipfile

import tqdm

import calendar_slicer.config.entrypoint.cis_ingest
import calendar_slicer.event_filter
import calendar_slicer.jsonl_writer
import calendar_slicer.source_reader

_LOGGER = logging.getLogger(__name__)


def main(argv=None):
    """Parse arguments, ingest calendar sources, and write JSONL output."""

    parser = argparse.ArgumentParser(
        prog=calendar_slicer.config.entrypoint.cis_ingest.PROG,
        description=calendar_slicer.config.entrypoint.cis_ingest.DESCRIPTION,
    )
    parser.add_argument(
        "input_path",
        help="Path to a single .ics file or a .zip archive containing .ics files.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        metavar="FILE",
        help="Write JSONL to FILE instead of stdout.",
    )
    parser.add_argument(
        "--maximum-age",
        dest="maximum_age_phrase",
        metavar="PHRASE",
        help='Discard events older than PHRASE (for example "10 weeks").',
    )
    parser.add_argument(
        "--earliest-timestamp",
        dest="earliest_timestamp_text",
        metavar="TIMESTAMP",
        help="Only include events whose start is at or after TIMESTAMP (ISO 8601).",
    )
    parser.add_argument(
        "--latest-timestamp",
        dest="latest_timestamp_text",
        metavar="TIMESTAMP",
        help="Only include events whose start is at or before TIMESTAMP (ISO 8601).",
    )

    args = parser.parse_args(argv)

    # Resolve the input path and collect event records.
    input_path = os.path.abspath(args.input_path)
    if not os.path.isfile(input_path):
        message = "input path is not a file: {input_path}".format(input_path=input_path)
        _LOGGER.error(message)
        sys.exit(1)

    try:
        ics_source_file_count = calendar_slicer.source_reader.count_ics_source_files(input_path)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        message = "failed to count ICS sources: {error}".format(error=error)
        _LOGGER.error(message)
        sys.exit(1)

    # Build optional start timestamp bounds before streaming records.
    try:
        earliest_inclusive, latest_inclusive = calendar_slicer.event_filter.build_event_time_bounds(
            maximum_age_phrase=args.maximum_age_phrase,
            earliest_timestamp_text=args.earliest_timestamp_text,
            latest_timestamp_text=args.latest_timestamp_text,
        )
    except ValueError as error:
        message = "invalid time filter: {error}".format(error=error)
        _LOGGER.error(message)
        sys.exit(1)

    # Track ingest progress on stderr so stdout stays JSONL-only.
    with tqdm.tqdm(
        total=ics_source_file_count,
        desc=calendar_slicer.config.entrypoint.cis_ingest.PROGRESS_DESCRIPTION,
        unit=calendar_slicer.config.entrypoint.cis_ingest.PROGRESS_UNIT,
        file=sys.stderr,
    ) as progress_bar:
        try:
            records = calendar_slicer.source_reader.iter_event_records(
                input_path,
                source_progress_callback=progress_bar.update,
            )
        except (OSError, ValueError, zipfile.BadZipFile) as error:
            message = "failed to read input: {error}".format(error=error)
            _LOGGER.error(message)
            sys.exit(1)

        filtered_records = calendar_slicer.event_filter.iter_matching_event_records(
            records,
            earliest_inclusive=earliest_inclusive,
            latest_inclusive=latest_inclusive,
        )

        # Write JSONL to the requested output destination.
        if args.output_path:
            output_directory = os.path.dirname(os.path.abspath(args.output_path))
            if output_directory:
                os.makedirs(output_directory, exist_ok=True)

            with open(args.output_path, "w", encoding="utf-8") as output_stream:
                calendar_slicer.jsonl_writer.write_jsonl(filtered_records, output_stream)
        else:
            calendar_slicer.jsonl_writer.write_jsonl(filtered_records, sys.stdout)
