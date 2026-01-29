"""Class definition for RpmPackageData."""

from __future__ import annotations

import re

from pathlib import Path
from typing import Any

import jmespath

from cyclonedx.model.component import Component

from choppr.types.package_data import PackageData
from choppr.types.shares import Shares
from choppr.utils.strings import remove_parenthesis, strings_match


__all__ = ["RpmPackageData"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


class RpmPackageData(PackageData):
    """Class containing frequently accessed information and the originating package."""

    def __init__(self, package: dict[str, Any]) -> None:
        """Create an instance of PackageDetails.

        Arguments:
            package: The originating package dictionary
        """
        self.package: dict[str, Any] = package
        self.name: str = package["name"]
        self.short_version: str = package["version"]["@ver"]
        self.release: str = package["version"]["@rel"]
        self.version: str = f"{self.short_version}-{self.release}"

    def provides_file(self, file: str, search_files: bool = False) -> bool:
        """Check if the package provides the given file.

        Arguments:
            file: The file to search for
            search_files: Flag to enable searching the files section (default False)

        Returns:
            bool: True if the file is provided by this package
        """
        # Search provides section
        if (
            package_provides := jmespath.search(
                expression=('format."rpm:provides"."rpm:entry"[*]."@name"'),
                data=self.package,
            )
        ) and any(
            strings_match(remove_parenthesis(provides), Path(file).name, Shares.options.allow_partial_filename_match)
            for provides in package_provides
        ):
            return True

        if search_files:
            # Search files
            if jmespath.search(
                expression=(f"format.file[?type(@) == 'string' && @ == '{file}']"),
                data=self.package,
            ):
                return True

            # Search directories
            directories: list[str] | None = jmespath.search(
                expression='format."file"[?"@type" == \'dir\']."#text"',
                data=self.package,
            )
            if directories and any(Path(file).is_relative_to(directory) for directory in directories):
                return True

        return False

    def requires(self) -> set[str]:
        """Get the files that the package requires.

        Returns:
            set[str]: The required files
        """
        if requirements := jmespath.search(
            expression='format."rpm:requires"."rpm:entry"[*]."@name"',
            data=self.package,
        ):
            return {requirement for requirement in requirements if requirement}

        return set()

    def __eq__(self, other: object) -> bool:
        match other:
            case RpmPackageData():
                return self.name == other.name and self.version == other.version
            case Component():
                if Shares.options.allow_version_mismatch:
                    return self.name == other.name
                if other.version is not None and (
                    version_match := re.match(r"^(?P<epoch_version>\d+:)?(?P<version>.*)$", other.version)
                ):
                    return self.name == other.name and self.version == version_match["version"]
            case {"name": _, "version": {"@ver": _}}:
                return self.name == str(other["name"]) and self.short_version == str(other["version"]["@ver"])  # type: ignore[index]
        return False

    __hash__ = PackageData.__hash__
