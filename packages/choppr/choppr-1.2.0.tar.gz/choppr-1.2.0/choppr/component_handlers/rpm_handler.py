"""Module for handling RPM packages."""

from __future__ import annotations

import gzip
import json
import lzma

from http import HTTPStatus
from typing import TYPE_CHECKING, Any, Final, cast

import jmespath
import xmltodict

from pydantic import HttpUrl

from choppr.component_handlers.purl_handler import PurlHandler
from choppr.decorators import limit_recursion
from choppr.types.enums import PurlType
from choppr.types.rpm_package_data import RpmPackageData
from choppr.types.shares import Shares
from choppr.utils import http
from choppr.utils.components import get_component_architecture, get_component_dependencies, get_purl_type
from choppr.utils.files import cache_file_outdated
from choppr.utils.logging import log_repo_pulls


if TYPE_CHECKING:
    from collections import OrderedDict
    from pathlib import Path

    from cyclonedx.model.component import Component

    from choppr.types.configuration import Repository


__all__ = ["RpmHandler"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


class RpmHandler(PurlHandler):
    """Class to handle all RPM repository processing."""

    def __init__(self) -> None:
        super().__init__(PurlType.RPM)

        self.repositories: dict[str, OrderedDict[str, Any]] = {}
        self.architecture_packages: dict[str, set[RpmPackageData]] = {}
        self.component_packages: dict[Component, set[RpmPackageData]] = {}

    ####################################################################################################
    # Exported Methods
    ####################################################################################################

    def cache_repositories(self) -> bool:
        """Pull all of the metadata for RPM repositories provided in the config.

        Returns:
            bool: True when any repository was successfully pulled
        """
        if rpm_repositories := Shares.repositories[self.purl_type]:
            expected = len(rpm_repositories)
            Shares.log.info(f"Caching {expected} RPM repositories...")

            for repo in rpm_repositories:
                if repo_return := self._get_remote_repo(repo):
                    repo_checksum, repo_data = repo_return
                    self.repositories[repo_checksum] = repo_data
            log_repo_pulls(expected, len(self.repositories), self.purl_type)

        return bool(len(self.repositories))

    def resolve_component_packages(self) -> None:
        """Resolve all RPM components to the packages in the repositories."""
        Shares.log.info(f"Resolving packages for {len(Shares.purl_components[self.purl_type])} RPM components")
        for component in Shares.purl_components[self.purl_type]:
            component_id = f"{component.name}-{component.version}"
            if packages := self._get_component_packages(component):
                if len(packages) == 1:
                    Shares.log.debug(f"Resolved the package for {component_id}")
                else:
                    Shares.log.warning(f"Resolved {len(packages)} packages for {component_id}")
                    for idx, package in enumerate(packages):
                        Shares.log.warning(f"    {idx}) {package}")
            else:
                Shares.log.warning(f"Unable to resolve a package for {component_id}")

            self.component_packages[component] = packages

    def populate_required_components(self, files: set[str]) -> None:
        """Determine which components provide the given files.

        Arguments:
            files: The files to search for in the component packages
        """
        required_packages: set[RpmPackageData] = set()

        for file in files:
            file_found = False
            for component in Shares.purl_components[self.purl_type]:
                if any(package.provides_file(file, True) for package in self.component_packages[component]):
                    file_found = True
                    if component not in self.required_components:
                        Shares.log.debug(f"Component required: {component.name}-{component.version}")
                        self.required_components.add(component)
                        required_packages.update(self.component_packages[component])

            if not file_found:
                Shares.log.warning(f"Unable to determine what component provides file: {file}")

        Shares.log.info(f"Found {len(self.required_components)} required RPM components")

        with self.cache_dir.joinpath("required-packages.txt").open("w", encoding="utf-8") as output:
            output.writelines([f"{pkg}\n" for pkg in sorted(required_packages, key=lambda p: p.name)])

    def populate_dependency_components(self) -> None:
        """Get all nested dependencies of the required components."""
        # Populate the dependencies from the dependencies section of the SBOM
        for component in self.allowlist_components | self.required_components:
            Shares.log.debug(f"Getting SBOM dependencies for {component.name}-{component.version}")
            amount_before = len(self.dependency_components)
            self._populate_nested_sbom_dependencies(component)
            Shares.log.debug(f"Found {len(self.dependency_components) - amount_before} new SBOM dependencies")

        sbom_dependency_count = len(self.dependency_components)
        Shares.log.info(f"Found {sbom_dependency_count} dependencies from the SBOM")

        # Check dependencies found in the package metadata
        for component in {
            c
            for c in self.allowlist_components | self.required_components | self.dependency_components
            if get_purl_type(c) is self.purl_type
        }:
            Shares.log.debug(f"Getting RPM dependencies for {component.name}-{component.version}")
            amount_before = len(self.dependency_components)
            self._populate_nested_file_dependencies(component)
            Shares.log.debug(f"Found {len(self.dependency_components) - amount_before} new RPM dependencies")

        Shares.log.info(f"Found {len(self.dependency_components) - sbom_dependency_count} RPM dependencies")

        dependency_packages = {
            package for component in self.dependency_components for package in self.component_packages[component]
        }

        with self.cache_dir.joinpath("dependency-packages.txt").open("w", encoding="utf-8") as file:
            file.writelines([f"{pkg}\n" for pkg in sorted(dependency_packages, key=lambda p: p.name)])

    ####################################################################################################
    # Utility Methods
    ####################################################################################################

    def _get_remote_repo(self, repo: Repository) -> tuple[str, OrderedDict[str, Any]] | None:
        repository_dir: Final[Path] = self.cache_dir.joinpath("repositories", f"{repo.url.host}{repo.url.path or ''}")
        repository_dir.mkdir(parents=True, exist_ok=True)

        cache_repomd = repository_dir / "repomd.json"
        repomd_url = HttpUrl(f"{repo.url}/repodata/repomd.xml")
        basic_auth, verify = http.get_auth_and_verify(repo.credentials, repo.certificate)

        if not cache_file_outdated(cache_repomd):
            Shares.log.info(f"Loading repository data from {cache_repomd}...")
            with cache_repomd.open() as file:
                repomd_data = cast("OrderedDict[str, Any]", json.load(file))
        else:
            Shares.log.info(f"Pulling repository data from {repomd_url}...")
            with http.get(repomd_url, basic_auth, verify) as response:
                if response.status_code > HTTPStatus.MULTIPLE_CHOICES:
                    Shares.log.error(f"Failed to pull repository: {response.content.decode()}")
                    return None

                repomd_data = xmltodict.parse(response.content)

                with cache_repomd.open("w") as file:
                    json.dump(repomd_data, file, indent=2)

        primary_checksum = jmespath.search(
            expression='[?"@type"==\'primary\'].checksum."#text"',
            data=repomd_data["repomd"]["data"],
        )
        primary_location = jmespath.search(
            expression='[?"@type"==\'primary\'].location."@href"',
            data=repomd_data["repomd"]["data"],
        )

        if isinstance(primary_checksum, list) and len(primary_checksum) == 1:
            cache_repository_file = repository_dir / f"{primary_checksum[0]}.json"

            # Use cached repository
            if cache_repository_file.is_file():
                with cache_repository_file.open() as file:
                    Shares.log.info("Successfully loaded repository from cache")
                    return (primary_checksum[0], cast("OrderedDict[str, Any]", json.load(file)))
            # Pull repository
            elif isinstance(primary_location, list) and len(primary_location) == 1:
                primary_url = HttpUrl(f"{repo.url}/{primary_location[0]}")
                with http.get(primary_url, basic_auth, verify) as primary_response:
                    if primary_response.status_code > HTTPStatus.MULTIPLE_CHOICES:
                        Shares.log.error(f"Failed to pull repository: {response.content.decode()}")
                        return None

                    match primary_url:
                        case _ if str(primary_url).endswith(".gz"):
                            primary_xml = gzip.decompress(primary_response.content)
                        case _ if str(primary_url).endswith(".xz"):
                            primary_xml = lzma.decompress(primary_response.content)
                        case _ if str(primary_url).endswith(".xml"):
                            primary_xml = primary_response.content
                        case _:
                            Shares.log.error(f"Unsupported file type found for primary repository: {primary_url}")
                            return None

                    Shares.log.info("Successfully pulled repository data")

                    repo_data = xmltodict.parse(primary_xml)
                    # Write repository data to cache
                    with cache_repository_file.open("w") as file:
                        json.dump(repo_data, file, indent=2)
                    return (primary_checksum[0], repo_data)

        Shares.log.error("Failed to get `location` and/or `checksum` from repository")
        return None

    def _get_component_packages(self, component: Component) -> set[RpmPackageData]:
        arch = get_component_architecture(component)

        if arch not in self.architecture_packages:
            self.architecture_packages[arch] = set()
            for repo in self.repositories.values():
                package_datas: set[RpmPackageData] = {
                    RpmPackageData(package)
                    for package in jmespath.search(expression=f"metadata.package[?arch == '{arch}']", data=repo)
                }

                self.architecture_packages[arch].update(package_datas)

        return {package for package in self.architecture_packages[arch] if package == component}

    def _populate_nested_sbom_dependencies(self, component: Component) -> None:
        for dependency in get_component_dependencies(component):
            if (
                dependency
                not in self.allowlist_components
                | self.denylist_components
                | self.required_components
                | self.dependency_components
            ):
                self.dependency_components.add(dependency)
                self._populate_nested_sbom_dependencies(dependency)

    @limit_recursion()
    def _populate_nested_file_dependencies(self, component: Component) -> None:
        new_dependencies: set[Component] = set()
        required_files = {file for package in self.component_packages[component] for file in package.requires()}
        unmatched_components = (
            self.component_packages.keys()
            - self.denylist_components
            - (self.allowlist_components | self.required_components | self.dependency_components)
        )

        for file in required_files:
            for unmatched_component in unmatched_components:
                if any(package.provides_file(file) for package in self.component_packages[unmatched_component]):
                    self.dependency_components.add(unmatched_component)
                    new_dependencies.add(unmatched_component)

        for dependency in new_dependencies:
            self._populate_nested_sbom_dependencies(dependency)

        for dependency in new_dependencies:
            self._populate_nested_file_dependencies(dependency)
