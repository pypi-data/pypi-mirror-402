"""Utility functions used when handling files."""

from __future__ import annotations

import json
import operator
import tarfile
import zipfile

from datetime import datetime
from functools import reduce
from typing import TYPE_CHECKING, Any

from pydantic import HttpUrl

from choppr.types.enums import OperatingMode
from choppr.types.shares import Shares
from choppr.utils import http


if TYPE_CHECKING:
    from pathlib import Path


__all__ = ["cache_file_outdated", "compress_directory", "extract_archive", "output_list", "version_existing_file"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


def _is_safe_to_extract(info: tarfile.TarInfo | zipfile.ZipInfo, output_dir: Path) -> bool:
    archived_file = info.name if isinstance(info, tarfile.TarInfo) else info.filename

    return output_dir.joinpath(archived_file).resolve().is_relative_to(output_dir.resolve())


def cache_file_outdated(file: Path) -> bool:
    """Check if the provided file is outdated.

    Arguments:
        file: File to check

    Returns:
        bool: True if the file is outdated, otherwise, false
    """
    if Shares.mode == OperatingMode.CACHE:
        Shares.log.debug(f"Running in cache mode. Refreshing file: {file.relative_to(Shares.options.cache_dir)}")
        return True

    if not file.is_file():
        Shares.log.debug(f"Missing cache file will be downloaded: {file.relative_to(Shares.options.cache_dir)}")
        return True

    if isinstance(Shares.options.cache_timeout, bool):
        Shares.log.debug(f"Cache timeout is {'enabled' if Shares.options.cache_timeout else 'disabled'}")
        return Shares.options.cache_timeout

    tz = datetime.now().astimezone().tzinfo
    expiration_time = datetime.fromtimestamp(file.stat().st_mtime, tz) + Shares.options.cache_timeout

    if outdated := expiration_time < datetime.now(tz):
        Shares.log.debug(f"Outdated cache file will be refreshed: {file.relative_to(Shares.options.cache_dir)}")

    return outdated


def compress_directory(archive: Path, input_dir: Path) -> None:
    """Compress all files in a given directory.

    Arguments:
        archive: The archive file to create
        input_dir: The directory to traverse and compress
    """
    match archive.suffix:
        case ".bz2":
            with tarfile.open(archive, "w:bz2") as archive_file:
                for file in input_dir.rglob("*"):
                    archive_file.add(file, file.relative_to(input_dir), False)
        case ".gz" | ".tgz":
            with tarfile.open(archive, "w:gz") as archive_file:
                for file in input_dir.rglob("*"):
                    archive_file.add(file, file.relative_to(input_dir), False)
        case ".xz":
            with tarfile.open(archive, "w:xz") as archive_file:
                for file in input_dir.rglob("*"):
                    archive_file.add(file, file.relative_to(input_dir), False)
        case ".zip":
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as archive_file:
                for file in input_dir.rglob("*"):
                    archive_file.write(file, file.relative_to(input_dir))


def extract_archive(archive: Path, output_dir: Path) -> None:
    """Extract the contents of the given archive to the output directory.

    Arguments:
        archive: The archive to extract
        output_dir: The output directory
    """
    match archive.suffix:
        case ".bz2":
            with tarfile.open(archive, "r:bz2") as archive_file:
                tar_members = [
                    member for member in archive_file.getmembers() if _is_safe_to_extract(member, output_dir)
                ]
                archive_file.extractall(output_dir, tar_members)  # noqa: S202
        case ".gz" | ".tgz":
            with tarfile.open(archive, "r:gz") as archive_file:
                tar_members = [
                    member for member in archive_file.getmembers() if _is_safe_to_extract(member, output_dir)
                ]
                archive_file.extractall(output_dir, tar_members)  # noqa: S202
        case ".xz":
            with tarfile.open(archive, "r:xz") as archive_file:
                tar_members = [
                    member for member in archive_file.getmembers() if _is_safe_to_extract(member, output_dir)
                ]
                archive_file.extractall(output_dir, tar_members)  # noqa: S202
        case ".zip":
            with zipfile.ZipFile(archive, "r", zipfile.ZIP_DEFLATED) as archive_file:
                zip_members = [member for member in archive_file.filelist if _is_safe_to_extract(member, output_dir)]
                archive_file.extractall(output_dir, zip_members)  # noqa: S202


def output_list(output_file: Path, items: list[str]) -> None:
    """Output list to the provided file.

    Arguments:
        output_file: Output file path
        items: List of strings to write to the file
    """
    with output_file.open("w", encoding="utf-8") as file:
        file.writelines([f"{item}\n" for item in items])


def schema_sort_json(source: dict[str, Any], schema_source: dict[str, Any] | HttpUrl) -> dict[str, Any]:
    """Sort the data in a JSON to match the schema.

    Arguments:
        source: The JSON to sort
        schema_source: The schema to use when sorting

    Returns:
        dict[str, Any]: The sorted JSON, or the original if the schema couldn't be pulled
    """
    if isinstance(schema_source, HttpUrl):
        if schema_data := http.download(schema_source):
            schema: dict[str, Any] = json.loads(schema_data)
        else:
            Shares.log.error(f"Unable to sort JSON: Failed to get schema from {schema_source}")
            return source
    else:
        schema = schema_source

    sorted_data: dict[str, Any] = {}
    for key in [k for k in schema["properties"] if k in source]:
        if "$ref" in schema["properties"][key] and (
            key_schema := _follow_json_ref(schema["properties"][key]["$ref"], schema)
        ):
            sorted_data[key] = schema_sort_json(source[key], key_schema)
        elif (
            isinstance(source[key], list)
            and "items" in schema["properties"][key]
            and "$ref" in schema["properties"][key]["items"]
            and (item_schema := _follow_json_ref(schema["properties"][key]["items"]["$ref"], schema))
        ):
            sorted_data[key] = [schema_sort_json(item, item_schema) for item in source[key]]
        else:
            sorted_data[key] = source[key]

    extra_data: dict[str, Any] = {key: source[key] for key in source if key not in schema["properties"]}

    return sorted_data | extra_data


def _follow_json_ref(ref: str, data: dict[str, Any]) -> dict[str, Any] | None:
    keys = ref.split("/")
    if "#" in keys:
        keys.remove("#")

    try:
        return reduce(operator.getitem, keys, data)
    except KeyError:
        return None


def version_existing_file(file: Path) -> Path:
    """If the provided path exists, append to the modification datetime, and create a new empty file.

    Arguments:
        file: The file to check

    Returns:
        Path: The provided file
    """
    if file.is_file() and file.read_text(encoding="utf-8", errors="ignore"):
        tz = datetime.now().astimezone().tzinfo
        modification_time = datetime.fromtimestamp(file.stat().st_mtime, tz)
        timestamp = modification_time.strftime("%Y-%m-%d-%H%M%S")

        versioned_file = file.parent.joinpath(f"{file.stem}-{timestamp}{''.join(file.suffixes)}")
        file.rename(versioned_file)

    file.touch()

    return file
