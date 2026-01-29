"""Utility functions used when for logging."""

from __future__ import annotations

from typing import TYPE_CHECKING

from choppr.constants import LOG_HEADER_LENGTH
from choppr.types.shares import Shares


if TYPE_CHECKING:
    from choppr.types.enums import PurlType


__all__ = [
    "log_header",
    "log_repo_pulls",
]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


def log_header(title: str) -> None:
    """Output a header to the log with the provided title, and padded with equal signs.

    Arguments:
        title: The header title
    """
    Shares.log.info(f" {title} ".center(LOG_HEADER_LENGTH, "="), stacklevel=2)


def log_repo_pulls(expected: int, actual: int, purl_type: PurlType) -> None:
    """Log the success or failure of pulling a repository.

    Arguments:
        expected: The expected number of repositories
        actual: The number of repositories actually pulled
        purl_type: They repository type
    """
    match actual:
        case 0:
            Shares.log.error(f"Failed to pull any {purl_type} repositories", stacklevel=2)
        case _ if actual == expected:
            Shares.log.info(f"Successfully pulled all {purl_type} repositories", stacklevel=2)
        case _:
            Shares.log.error(f"Failed to pull {expected - actual}/{expected} {purl_type} repositories", stacklevel=2)
