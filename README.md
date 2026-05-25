# calendar_slicer

Translate calendar events from ICS files and ZIP archives of ICS files to flat JSONL data.

Each output record contains the event name, calendar name, and ISO 8601 start/stop timestamps. The `cis_ingest` CLI accepts a single `.ics` file or a `.zip` archive containing nested folders and `.ics` files.

This was created in order to take the blobs of calendar data that Google Calendar exports, flatten them to a simple list of events, and slice by certain ranges of time.

## Requirements

- Python 3.11+

## Installation

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

For development (includes pytest):

```bash
.venv/bin/pip install -e ".[dev]"
```

## Usage

Ingest one ICS file and print JSONL to stdout:

```bash
cis_ingest /path/to/calendar.ics
```

Ingest a ZIP archive and write JSONL to a file:

```bash
cis_ingest /path/to/calendars.zip --output events.jsonl
```

Filter events by time window:

```bash
cis_ingest calendars.zip \
  --maximum-age "10 weeks" \
  --earliest-timestamp "2025-01-01T00:00:00+00:00" \
  --latest-timestamp "2026-12-31T23:59:59+00:00" \
  --output recent.jsonl
```

Progress is reported on stderr (one step per ICS file) so stdout stays clean JSONL when writing to a pipe or redirect.

## CLI options

| Option | Description |
| --- | --- |
| `input_path` | Path to a `.ics` file or `.zip` archive |
| `--output FILE` | Write JSONL to `FILE` instead of stdout |
| `--maximum-age PHRASE` | Drop events whose start is before `now − PHRASE` |
| `--earliest-timestamp TIMESTAMP` | Keep events with start ≥ `TIMESTAMP` (ISO 8601) |
| `--latest-timestamp TIMESTAMP` | Keep events with start ≤ `TIMESTAMP` (ISO 8601) |

When both `--maximum-age` and `--earliest-timestamp` are set, the later cutoff applies.

### `--maximum-age` phrases

Use a count and unit, for example:

- `"10 weeks"`
- `"3 days"`
- `"6 months"`
- `"1 year"`

Supported units include seconds, minutes, hours, days, weeks, months, and years.

## Output format

Each line is one JSON object:

```json
{"name": "Team Standup", "calendar": "Work Calendar", "start_timestamp": "2025-01-15T10:00:00+00:00", "stop_timestamp": "2025-01-15T10:30:00+00:00"}
```

| Field | Source |
| --- | --- |
| `name` | Event `SUMMARY` (empty string if missing) |
| `calendar` | `X-WR-CALNAME`, `NAME`, parent folder name, or `.ics` filename stem |
| `start_timestamp` | `DTSTART` as ISO 8601 |
| `stop_timestamp` | `DTEND`, or `DTSTART` + `DURATION`, or all-day end (+1 day) |

Time filters apply to `start_timestamp`.

## Development

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
  entrypoint/cis_ingest.py
tests/
```
