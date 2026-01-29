"""Class definition for PackageData."""

from __future__ import annotations

import abc

from hashlib import sha256
from typing import Any

from cyclonedx.model.component import Component

from choppr.types.shares import Shares


__all__ = ["PackageData"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


class PackageData(abc.ABC):
    """Abstract base class for package data, providing common functionality for package metadata."""

    def __init__(self, package: Any) -> None:  # noqa: ANN401
        """Initialize the PackageData with the originating package.

        Arguments:
            package: The originating package data (e.g., dictionary for RPM, BinaryPackage for Debian)
        """
        self.package: Any = package
        self.name: str = ""
        self.version: str = ""

    @abc.abstractmethod
    def provides_file(self, file: str) -> bool:
        """Check if the package provides the given file.

        Arguments:
            file: The file to search for

        Returns:
            bool: True if the file is provided by this package
        """

    def __eq__(self, other: object) -> bool:
        match other:
            case PackageData():
                return self.name == other.name and self.version == other.version
            case Component():
                if Shares.options.allow_version_mismatch:
                    return self.name == other.name
                if other.version is not None:
                    return self.name == other.name and self.version == other.version

        return False

    def __hash__(self) -> int:
        sha = sha256()
        sha.update(self.name.encode())
        sha.update(self.version.encode())
        return int(sha.hexdigest(), 16)

    def __str__(self) -> str:
        return f"{self.name}-{self.version}"
