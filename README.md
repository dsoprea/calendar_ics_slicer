# Overview

Translate calendar events from ICS files and ZIP archives of ICS files to flat JSONL data.

Each output record contains the event id, event name, calendar name, and ISO 8601 start/stop timestamps. The `cis_ingest` CLI accepts a single `.ics` file or a `.zip` archive containing nested folders and `.ics` files.

This was created in order to take the blobs of calendar data that Google Calendar exports, flatten them to a simple list of events, and slice by certain ranges of time.

# Requirements

- Python 3.11+

# Installation

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

For development (includes pytest):

```bash
.venv/bin/pip install -e ".[dev]"
```

# Usage

Ingest one ICS file and print JSONL to stdout:

```bash
cis_ingest /path/to/calendar.ics
```

Example stdout:

```json
{"event_id": "abc123@google.com", "name": "Team Standup", "calendar": "Work Calendar", "start_timestamp": "2025-01-15T10:00:00+00:00", "stop_timestamp": "2025-01-15T10:30:00+00:00"}
{"event_id": "def456@google.com", "name": "Dentist", "calendar": "Personal", "start_timestamp": "2025-02-03T14:00:00+00:00", "stop_timestamp": "2025-02-03T15:00:00+00:00"}
```

Ingest a ZIP archive and write JSONL to a file:

```bash
cis_ingest /path/to/calendars.zip --output events.jsonl
```

`events.jsonl` contains the same one-object-per-line JSONL format as stdout.

Filter events by time window:

```bash
cis_ingest calendars.zip \
  --maximum-age "10 weeks" \
  --earliest-timestamp "2025-01-01T00:00:00+00:00" \
  --latest-timestamp "2026-12-31T23:59:59+00:00" \
  --output recent.jsonl
```

Example `recent.jsonl` (only events whose start falls in the window):

```json
{"event_id": "abc123@google.com", "name": "Team Standup", "calendar": "Work Calendar", "start_timestamp": "2025-01-15T10:00:00+00:00", "stop_timestamp": "2025-01-15T10:30:00+00:00"}
```

Write each event as JSON under a year directory keyed by local start time:

```bash
cis_ingest calendars.zip \
  --output events.jsonl \
  --output-bin-path /path/to/event-bins
```

Example layout (assuming the local timezone is `UTC-05:00`):

```
/path/to/event-bins/
  2025/
    abc123@google.com.json
    def456@google.com.json
```

Example `/path/to/event-bins/2025/abc123@google.com.json`:

```json
{"event_id": "abc123@google.com", "name": "Team Standup", "calendar": "Work Calendar", "start_timestamp": "2025-01-15T05:00:00-05:00", "stop_timestamp": "2025-01-15T10:30:00+00:00"}
```

Progress is reported on stderr (one step per ICS file) so stdout stays clean JSONL when writing to a pipe or redirect. Log messages at WARNING and above are written to stderr; the default log level is WARNING.

Example stderr while ingesting:

```
Ingesting ICS files: 100%|██████████| 3/3 [00:00<00:00, 120.00file/s]
```

Example stderr when an event lacks a UID:

```
ERROR:calendar_slicer.ics_parser:skipping event without UID: calendar=Work Calendar summary=Untitled
```

# CLI options

| Option | Description |
| --- | --- |
| `input_path` | Path to a `.ics` file or `.zip` archive |
| `--output FILE` | Write JSONL to `FILE` instead of stdout |
| `--output-bin-path PATH` | Write each event as `PATH/<local-start-year>/<event_id>.json` with `start_timestamp` in the local timezone |
| `--maximum-age PHRASE` | Drop events whose start is before `now − PHRASE` |
| `--earliest-timestamp TIMESTAMP` | Keep events with start ≥ `TIMESTAMP` (ISO 8601) |
| `--latest-timestamp TIMESTAMP` | Keep events with start ≤ `TIMESTAMP` (ISO 8601) |

When both `--maximum-age` and `--earliest-timestamp` are set, the later cutoff applies.

## `--maximum-age` phrases

Use a count and unit, for example:

- `"10 weeks"`
- `"3 days"`
- `"6 months"`
- `"1 year"`

Supported units include seconds, minutes, hours, days, weeks, months, and years.

# Output format

Each line is one JSON object:

```json
{"event_id": "event-1", "name": "Team Standup", "calendar": "Work Calendar", "start_timestamp": "2025-01-15T10:00:00+00:00", "stop_timestamp": "2025-01-15T10:30:00+00:00"}
```

| Field | Source |
| --- | --- |
| `event_id` | Event `UID` (required; events without a UID are skipped and logged as errors) |
| `name` | Event `SUMMARY` (empty string if missing) |
| `calendar` | `X-WR-CALNAME`, `NAME`, parent folder name, or `.ics` filename stem |
| `start_timestamp` | `DTSTART` as ISO 8601 |
| `stop_timestamp` | `DTEND`, or `DTSTART` + `DURATION`, or all-day end (+1 day) |

Time filters apply to `start_timestamp`.

## Binned JSON output

When `--output-bin-path` is set, each event is also written as one JSON file at:

```
<output-bin-path>/<local-start-year>/<event_id>.json
```

The binned JSON uses the same fields as JSONL output, except `start_timestamp` is converted to the system local timezone. JSONL output (stdout or `--output`) keeps the original parsed timestamps. Existing binned files at the target path are not overwritten.

# Development

Run tests:

```bash
.venv/bin/python -m pytest -q
```

Project layout:

```
src/calendar_slicer/
  ics_parser.py          # ICS parsing
  source_reader.py       # .ics and .zip input
  event_filter.py        # time window filtering
  time_phrase.py         # interval phrase parsing
  timestamp_utility.py   # ISO 8601 parsing
  jsonl_writer.py        # JSONL output
  event_bin_writer.py    # per-event JSON bins by local start year
  entrypoint/cis_ingest.py
tests/
```
