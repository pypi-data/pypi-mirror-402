"""Class definition for DebPackageData."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cyclonedx.model.component import Component
from debian.debian_support import Version

from choppr.apt_api import BinaryPackage
from choppr.types.package_data import PackageData
from choppr.types.shares import Shares
from choppr.utils.components import get_component_architecture
from choppr.utils.strings import strings_match


if TYPE_CHECKING:
    from choppr.apt_api.dependency import Dependency


__all__ = ["DebPackageData"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


class DebPackageData(PackageData):
    """Class containing frequently accessed information and the originating package.

    Members:
        - name
        - package
        - version
    """

    def __init__(self, package: BinaryPackage) -> None:
        """Create an instance of DebPackageData.

        Arguments:
            package: The originating binary package
        """
        self.package: BinaryPackage = package
        self.name: str = package.package
        self.version: str = package.version

    def provides_file(self, file: str) -> bool:
        """Check if the package provides the given file.

        Arguments:
            file: The file to search for

        Returns:
            bool: True if the file is provided by this package
        """
        return any(strings_match(provided_file, file, True) for provided_file in self.package.provides)

    def satisfies_dependency(self, dependency: Dependency) -> bool:
        """Check if the package satisfies the given dependency.

        Arguments:
            dependency: The dependency to check against.

        Returns:
            bool: True if the depencency is satisfied by this package
        """
        return self.name == dependency.name and self._version_match(dependency.version)

    def is_essential(self, build_essential: bool = False) -> bool:
        """Check if the package is essential.

        Arguments:
            build_essential: Enable checking build essential packages (default False)

        Returns:
            bool: True if package is essential
        """
        return bool(
            self.package.essential
            or (build_essential and self.package.build_essential)
            or (self.package.priority and self.package.priority.lower() == "required")
        )

    @staticmethod
    def _get_min_max_version(versions: list[str], symbol: str) -> tuple[bool, Version | None]:
        return next(
            (("=" in v, Version(v.replace(symbol, "").replace("=", "").strip())) for v in versions if symbol in v),
            (False, None),
        )

    def _get_max_version(self, versions: list[str]) -> tuple[bool, Version | None]:
        return self._get_min_max_version(versions, "<")

    def _get_min_version(self, versions: list[str]) -> tuple[bool, Version | None]:
        return self._get_min_max_version(versions, ">")

    def _version_within_max(self, versions: list[str]) -> bool:
        can_be_equal, max_version = self._get_max_version(versions)

        if max_version is None:
            Shares.log.debug(f"No valid maximum version: {', '.join(versions)}")
            return False

        return (can_be_equal and Version(self.package.version) <= max_version) or (
            not can_be_equal and Version(self.package.version) < max_version
        )

    def _version_within_min(self, versions: list[str]) -> bool:
        can_be_equal, min_version = self._get_min_version(versions)

        if min_version is None:
            Shares.log.debug(f"No valid minimum version: {', '.join(versions)}")
            return False

        return (can_be_equal and Version(self.package.version) >= min_version) or (
            not can_be_equal and Version(self.package.version) > min_version
        )

    def _version_within_range(self, versions: list[str]) -> bool:
        within_max = self._version_within_max(versions)
        within_min = self._version_within_min(versions)

        return within_max and within_min

    def _version_match(self, version: str) -> bool:
        # sourcery skip: assign-if-exp, reintroduce-else
        if version.startswith("="):
            exact_version = Version(version.replace("=", "").strip())
            return Version(self.package.version) == exact_version
        if all(sign in version for sign in ["<", ">"]):
            return self._version_within_range(version.split(","))
        if version.startswith("<"):
            return self._version_within_max([version])
        if version.startswith(">"):
            return self._version_within_min([version])

        return True

    def __eq__(self, other: object) -> bool:
        match other:
            case DebPackageData():
                return self.name == other.name and self.version == other.version
            case BinaryPackage():
                return self.name == str(other.package) and self.version == str(other.version)
            case Component():
                architecture_matches = True
                if self.package.architecture:
                    architecture_matches = self.package.architecture == get_component_architecture(other)
                if Shares.options.allow_version_mismatch:
                    return self.name == other.name and architecture_matches
                if other.version is not None:
                    return self.name == other.name and self.version == other.version and architecture_matches

        return False

    __hash__ = PackageData.__hash__
