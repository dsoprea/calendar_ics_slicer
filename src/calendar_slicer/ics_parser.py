"""Parse ICS calendar data into normalized event record dictionaries."""

import datetime
import logging

import icalendar

_LOGGER = logging.getLogger(__name__)


def _read_calendar_property(calendar_component, property_name):
    """Return a string calendar property value when present."""

    if property_name not in calendar_component:
        return None

    return str(calendar_component[property_name])


def _resolve_calendar_name(calendar_component, folder_name, ics_basename):
    """Resolve the calendar display name from ICS metadata and path hints."""

    calendar_name = _read_calendar_property(calendar_component, "X-WR-CALNAME")
    if calendar_name:
        return calendar_name

    calendar_name = _read_calendar_property(calendar_component, "NAME")
    if calendar_name:
        return calendar_name

    if folder_name:
        return folder_name

    if ics_basename.lower().endswith(".ics"):
        return ics_basename[:-4]

    return ics_basename


def _instant_to_iso8601(instant):
    """Convert a date or datetime value to an ISO 8601 timestamp string."""

    if isinstance(instant, datetime.datetime):
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=datetime.timezone.utc)

        return instant.isoformat()

    if isinstance(instant, datetime.date):
        combined = datetime.datetime.combine(
            instant,
            datetime.time.min,
            tzinfo=datetime.timezone.utc,
        )

        return combined.isoformat()

    message = "unsupported instant type {instant_type}".format(instant_type=type(instant))
    raise TypeError(message)


def _read_event_summary(event_component):
    """Return the event summary string, or an empty string when absent."""

    if "SUMMARY" not in event_component:
        return ""

    return str(event_component["SUMMARY"])


def _read_event_id(event_component):
    """Return the event UID string, or None when absent or empty."""

    if "UID" not in event_component:
        return None

    event_id = str(event_component["UID"])
    if not event_id:
        return None

    return event_id


def _read_event_start(event_component):
    """Return the DTSTART value for an event, or None when absent."""

    if "DTSTART" not in event_component:
        return None

    return event_component.decoded("DTSTART")


def _read_event_stop(event_component, start_instant):
    """Return the event stop instant from DTEND, DURATION, or all-day rules."""

    if "DTEND" in event_component:
        return event_component.decoded("DTEND")

    if "DURATION" in event_component:
        duration = event_component.decoded("DURATION")
        if isinstance(start_instant, datetime.datetime):
            return start_instant + duration

        if isinstance(start_instant, datetime.date):
            start_datetime = datetime.datetime.combine(
                start_instant,
                datetime.time.min,
                tzinfo=datetime.timezone.utc,
            )
            stop_datetime = start_datetime + duration

            return stop_datetime.date()

    if isinstance(start_instant, datetime.date):
        return start_instant + datetime.timedelta(days=1)

    return start_instant


def _build_event_record(calendar_name, event_component):
    """Build one JSONL-ready event record from a VEVENT component."""

    start_instant = _read_event_start(event_component)
    if start_instant is None:
        return None

    # Reject events that lack a usable UID.
    event_id = _read_event_id(event_component)
    if event_id is None:
        summary = _read_event_summary(event_component)
        message = "skipping event without UID: calendar={calendar_name} summary={summary}".format(
            calendar_name=calendar_name,
            summary=summary,
        )
        _LOGGER.error(message)

        return None

    stop_instant = _read_event_stop(event_component, start_instant)
    summary = _read_event_summary(event_component)

    record = {
        "event_id": event_id,
        "name": summary,
        "calendar": calendar_name,
        "start_timestamp": _instant_to_iso8601(start_instant),
        "stop_timestamp": _instant_to_iso8601(stop_instant),
    }

    return record


def parse_ics_bytes(ics_bytes, folder_name, ics_basename):
    """Parse ICS bytes and yield event record dictionaries."""

    calendar = icalendar.Calendar.from_ical(ics_bytes)
    calendar_name = _resolve_calendar_name(calendar, folder_name, ics_basename)

    # Walk each VEVENT and emit normalized records.
    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        record = _build_event_record(calendar_name, component)
        if record is None:
            continue

        yield record
