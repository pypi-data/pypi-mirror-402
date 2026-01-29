"""Class definition for PurlHandler."""

from __future__ import annotations

import abc
import logging

from typing import TYPE_CHECKING

from choppr.types.shares import Shares


if TYPE_CHECKING:
    from pathlib import Path

    from cyclonedx.model.component import Component

    from choppr.types.enums import PurlType


__all__ = ["PurlHandler"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


class PurlHandler(abc.ABC):
    """Base class for handling package repositories of different PURL types."""

    def __init__(self, purl_type: PurlType) -> None:
        """Initialize the PurlHandler with a specific PURL type.

        Arguments:
            purl_type: The type of package URL (e.g., RPM, NPM, PyPI).
        """
        self.purl_type: PurlType = purl_type
        self.cache_dir: Path = Shares.options.cache_dir / purl_type.value.lower()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.allowlist_components: set[Component] = set()
        self.denylist_components: set[Component] = set()
        self.required_components: set[Component] = set()
        self.dependency_components: set[Component] = set()

    @abc.abstractmethod
    def cache_repositories(self) -> bool:
        """Pull metadata for repositories of the specified PURL type.

        Returns:
            bool: True if any repository was successfully pulled, False otherwise.
        """

    @abc.abstractmethod
    def resolve_component_packages(self) -> None:
        """Resolve all components to their packages in the repositories."""

    def resolve_allowlist_denylist(self) -> None:
        """Resolve all components in the allowlist and denylist."""
        if allowlist := list(Shares.options.allowlist.get(self.purl_type, set())):
            self.allowlist_components = {c for c in Shares.purl_components[self.purl_type] if c in allowlist}
        if denylist := list(Shares.options.denylist.get(self.purl_type, set())):
            self.denylist_components = {c for c in Shares.purl_components[self.purl_type] if c in denylist}

        if Shares.log.level is logging.DEBUG:
            for component in self.allowlist_components:
                Shares.log.debug(f"Component in allowlist: {component.name}-{component.version}")
            for component in self.denylist_components:
                Shares.log.debug(f"Component in denylist: {component.name}-{component.version}")

        if self.allowlist_components:
            count = len(self.allowlist_components)
            Shares.log.info(f"Added {count} {self.purl_type} component{'' if count == 1 else 's'} to the allowlist")
        if self.denylist_components:
            count = len(self.denylist_components)
            Shares.log.info(f"Added {count} {self.purl_type} component{'' if count == 1 else 's'} to the denylist")

    @abc.abstractmethod
    def populate_required_components(self, files: set[str]) -> None:
        """Determine which components provide the given files.

        Arguments:
            files: The files to search for in the component packages
        """

    @abc.abstractmethod
    def populate_dependency_components(self) -> None:
        """Get all nested dependencies of the required components."""
