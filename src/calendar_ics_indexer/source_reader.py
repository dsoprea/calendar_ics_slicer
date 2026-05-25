"""Read ICS content from a single file path or a ZIP archive."""

import logging
import os
import zipfile

import calendar_ics_indexer.ics_parser

_LOGGER = logging.getLogger(__name__)


def _is_ics_member(member_name):
    """Return True when a ZIP member path ends with the .ics extension."""

    lowered = member_name.lower()

    return lowered.endswith(".ics")


def _folder_name_for_member(member_name):
    """Return the parent directory name for a ZIP member path."""

    directory_name = os.path.dirname(member_name)
    if not directory_name:
        return ""

    return os.path.basename(directory_name)


def _basename_for_member(member_name):
    """Return the basename for a ZIP member path."""

    return os.path.basename(member_name)


def _list_ics_member_names_from_zip(zip_path):
    """Return ICS member paths contained in a ZIP archive."""

    with zipfile.ZipFile(zip_path, "r") as archive:
        member_names = archive.namelist()

    ics_member_names = []
    for member_name in member_names:
        if member_name.endswith("/"):
            continue

        if not _is_ics_member(member_name):
            continue

        ics_member_names.append(member_name)

    return ics_member_names


def _read_member_bytes(archive, member_name):
    """Read one ZIP member into bytes."""

    with archive.open(member_name, "r") as member_stream:
        member_bytes = member_stream.read()

    return member_bytes


def _folder_name_for_file_path(file_path):
    """Return the parent directory basename for a filesystem ICS path."""

    directory_name = os.path.dirname(file_path)
    if not directory_name:
        return ""

    return os.path.basename(directory_name)


def _basename_for_file_path(file_path):
    """Return the basename for a filesystem ICS path."""

    return os.path.basename(file_path)


def _read_file_bytes(file_path):
    """Read a filesystem ICS file into bytes."""

    with open(file_path, "rb") as input_stream:
        file_bytes = input_stream.read()

    return file_bytes


def _notify_source_progress(source_progress_callback):
    """Invoke the optional per-source progress callback."""

    if source_progress_callback is None:
        return

    source_progress_callback(1)


def count_ics_source_files(input_path):
    """Return how many ICS sources the input path contains."""

    lowered_path = input_path.lower()

    if lowered_path.endswith(".zip"):
        ics_member_names = _list_ics_member_names_from_zip(input_path)

        return len(ics_member_names)

    if lowered_path.endswith(".ics"):
        return 1

    message = "unsupported input path extension for {input_path}".format(input_path=input_path)
    raise ValueError(message)


def iter_event_records(input_path, source_progress_callback=None):
    """Yield event record dictionaries from an ICS file or ZIP archive path."""

    lowered_path = input_path.lower()

    if lowered_path.endswith(".zip"):
        ics_member_names = _list_ics_member_names_from_zip(input_path)

        with zipfile.ZipFile(input_path, "r") as archive:
            for member_name in ics_member_names:
                folder_name = _folder_name_for_member(member_name)
                ics_basename = _basename_for_member(member_name)
                ics_bytes = _read_member_bytes(archive, member_name)
                records = calendar_ics_indexer.ics_parser.parse_ics_bytes(
                    ics_bytes,
                    folder_name,
                    ics_basename,
                )

                for record in records:
                    yield record

                _notify_source_progress(source_progress_callback)

        return

    if lowered_path.endswith(".ics"):
        folder_name = _folder_name_for_file_path(input_path)
        ics_basename = _basename_for_file_path(input_path)
        ics_bytes = _read_file_bytes(input_path)
        records = calendar_ics_indexer.ics_parser.parse_ics_bytes(
            ics_bytes,
            folder_name,
            ics_basename,
        )

        for record in records:
            yield record

        _notify_source_progress(source_progress_callback)

        return

    message = "unsupported input path extension for {input_path}".format(input_path=input_path)
    raise ValueError(message)
