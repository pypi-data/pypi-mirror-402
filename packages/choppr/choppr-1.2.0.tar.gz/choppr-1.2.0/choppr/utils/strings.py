"""Utility functions used when performing string manipulations and comparisons."""

from __future__ import annotations

import re


__all__ = [
    "deduplicate_slashes",
    "normalize_slashes",
    "prepend_slash",
    "remove_parenthesis",
    "strings_match",
]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


def deduplicate_slashes(value: str) -> str:
    """De-duplicate repeated slashes in a string.

    This should be run after `normalize_slashes`, so there are only forward slashes in a string.

    Arguments:
        value: A string contianing repeated slashes

    Returns:
        str: The value with repeated slahes de-duplicated
    """
    return re.sub(r"/{2,}", "/", value)


def normalize_slashes(value: str) -> str:
    """Convert all backslashes to forward slashes.

    Arguments:
        value: A string containing slashes

    Returns:
        str: The value with all backslashes replaced with forward slashes
    """
    return value.replace(r"\\", "/")


def prepend_slash(value: str) -> str:
    """Prepend a slash to a string that doesn't have one.

    Arguments:
        value: A string to prepend a slash to

    Returns:
        str: The string with a prepended slash
    """
    return f"/{value.removeprefix('/')}"


def remove_parenthesis(value: str) -> str:
    """Remove text within parenthesis, to include empty parenthesis.

    Arguments:
        value: Text to remove parenthesis from

    Returns:
        str: Text with parenthesis removed
    """
    return_value = value
    while re.search(r"\([^\(\)]*?\)", return_value):
        return_value = re.sub(r"\([^\(\)]*?\)", "", return_value)
    return return_value.strip()


def strings_match(left: str, right: str, allow_partial_match: bool = False) -> bool:
    """Compare the given strings to check if they match.

    Arguments:
        left: The string to compare to
        right: The string to compare against
        allow_partial_match: Allow partial matching of the strings (default False)

    Returns:
        bool: True if the strings match
    """
    if left == right:
        return True

    if not left or not right:
        return False

    return left in right or right in left if allow_partial_match else False
