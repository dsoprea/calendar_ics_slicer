"""Filter event records by start timestamp bounds."""

import datetime
import logging

import calendar_slicer.time_phrase
import calendar_slicer.timestamp_utility

_LOGGER = logging.getLogger(__name__)


def build_event_time_bounds(
    maximum_age_phrase=None,
    earliest_timestamp_text=None,
    latest_timestamp_text=None,
    reference_instant=None,
):
    """Return inclusive earliest and latest bounds for event start timestamps."""

    earliest_inclusive = None
    latest_inclusive = None

    # Apply an explicit earliest timestamp bound when provided.
    if earliest_timestamp_text is not None:
        earliest_inclusive = calendar_slicer.timestamp_utility.parse_iso8601_timestamp(
            earliest_timestamp_text,
        )

    # Apply an explicit latest timestamp bound when provided.
    if latest_timestamp_text is not None:
        latest_inclusive = calendar_slicer.timestamp_utility.parse_iso8601_timestamp(
            latest_timestamp_text,
        )

    # Derive a rolling cutoff from maximum age and merge with earliest bounds.
    if maximum_age_phrase is not None:
        if reference_instant is None:
            reference_instant = datetime.datetime.now(datetime.timezone.utc)

        maximum_age_cutoff = calendar_slicer.time_phrase.subtract_time_phrase(
            reference_instant,
            maximum_age_phrase,
        )

        if earliest_inclusive is None:
            earliest_inclusive = maximum_age_cutoff
        elif maximum_age_cutoff > earliest_inclusive:
            earliest_inclusive = maximum_age_cutoff

    return earliest_inclusive, latest_inclusive


def iter_matching_event_records(records, earliest_inclusive=None, latest_inclusive=None):
    """Yield event records whose start timestamp falls within the bounds."""

    # Drop records outside the configured start timestamp window.
    for record in records:
        start_instant = calendar_slicer.timestamp_utility.parse_iso8601_timestamp(
            record["start_timestamp"],
        )

        if earliest_inclusive is not None and start_instant < earliest_inclusive:
            continue

        if latest_inclusive is not None and start_instant > latest_inclusive:
            continue

        yield record
