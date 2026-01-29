"""PackagesFile implementation."""

from __future__ import annotations

import json

from typing import TYPE_CHECKING

from choppr.apt_api._utils import get_value
from choppr.apt_api.binary_package import BinaryPackage
from choppr.types.enums import OperatingMode, PurlType
from choppr.types.shares import Shares


if TYPE_CHECKING:
    from pathlib import Path

    from pydantic import HttpUrl


__all__ = ["PackagesFile"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


def _get_file_list(binary_package: BinaryPackage) -> list[str]:
    Shares.log.debug(f"Package not found in contents file, getting provided files: {binary_package.package}")
    try:
        if package_file_list := binary_package.provides:
            return package_file_list
    except ConnectionError:
        Shares.log.warning(f"Failed to get file list for {binary_package.package}, continuing...")

    return []


class PackagesFile:
    """Class that represents a Packages file."""

    def __init__(self, packages_file: Path, content_file: Path, repo_url: HttpUrl) -> None:
        """Initialize an instance of PackagesFile.

        Arguments:
            packages_file: The list of packages with their metadata
            content_file: The list of files internal to this specific package
            repo_url: The URL for the repository
        """
        self.packages: set[BinaryPackage] = set()

        if packages_file.is_file():
            with packages_file.open(encoding="utf-16") as f:
                content = f.read().strip()

            with content_file.open(encoding="utf-8") as f:
                file_list: dict[str, list[str]] = json.load(f)

            file_list_updated = False

            if packages_data := content.split("\n\n"):
                for package_data in [p for p in packages_data if p]:
                    name = str(get_value(package_data, "Package"))
                    if name in file_list:
                        bp = BinaryPackage(package_data, repo_url, file_list[name])
                    else:
                        bp = BinaryPackage(package_data, repo_url)

                        if (
                            Shares.mode == OperatingMode.CACHE
                            and any(c for c in Shares.purl_components[PurlType.DEB] if c.name == name)
                            and (package_file_list := _get_file_list(bp))
                        ):
                            file_list[name] = package_file_list
                            file_list_updated = True

                    self.packages.add(bp)

            if file_list_updated:
                with content_file.open("w", encoding="utf-8") as f:
                    json.dump(file_list, f, cls=json.JSONEncoder, indent=2)
