"""Module containing functions to call strace and analyze output."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

from choppr.utils.strings import deduplicate_slashes, normalize_slashes


if TYPE_CHECKING:
    from pathlib import Path


__all__ = ["get_files"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "Lockheed Martin Proprietary Information"


def _resolve_relative_path(path: str) -> str:
    absolute_path = path
    relative_path_pattern = r"(?P<parent>/[^/]+?/\.\.)|(?P<current>(?<=/)\.(?:/|$))"

    while re.search(relative_path_pattern, absolute_path):
        absolute_path = re.sub(relative_path_pattern, "", absolute_path)

    return absolute_path


def _clean_path(path: str) -> str:
    clean_path = normalize_slashes(path)
    clean_path = deduplicate_slashes(clean_path)
    return _resolve_relative_path(clean_path)


def get_files(strace_location: Path) -> set[str]:
    """Get the list of touched files from strace.

    Arguments:
        strace_location: Output file from strace

    Returns:
        set[str]: Set of touched files
    """
    with strace_location.open(encoding="utf-8") as file:
        text = file.read()

    flags = re.MULTILINE | re.IGNORECASE

    dir_regex = (
        r"^.*?"
        r"(?:(?:mkdir).*?"
        r"(?:(?:\'|\")(?P<mkdir>.*?)(?:\'|\")))"
        r"|"
        r"(?:(?:(?:\'|\")(?P<dirname>.*?)(?:\'|\"))"
        r"(?=.*?(?:S_IFDIR|O_DIRECTORY))(?!.*(?:ENOENT|unfinished)))"
    )
    dir_matches = re.finditer(dir_regex, text, flags)
    directories: set[str] = {
        _clean_path(dm.group(g)) for dm in dir_matches for g in ["dirname", "mkdir"] if dm.group(g) is not None
    }

    regex = r"^.*?(?:(?:\'|\")(?P<filename>.+?)(?:\'|\"))(?!.*(?:S_IFDIR|ENOENT|O_DIRECTORY|unfinished))"
    files: set[str] = {_clean_path(match.group("filename")) for match in re.finditer(regex, text, flags)}
    return files - directories
