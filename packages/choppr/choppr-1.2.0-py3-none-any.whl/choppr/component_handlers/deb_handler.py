"""Module for handling DEB packages."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from pydantic import TypeAdapter

from choppr import apt_api
from choppr.component_handlers.purl_handler import PurlHandler
from choppr.decorators import limit_recursion
from choppr.types.configuration import DebianRepository
from choppr.types.deb_package_data import DebPackageData
from choppr.types.enums import PurlType
from choppr.types.shares import Shares
from choppr.utils import http
from choppr.utils.components import get_component_architecture, get_component_dependencies, get_purl_type
from choppr.utils.logging import log_repo_pulls


if TYPE_CHECKING:
    from pathlib import Path

    from cyclonedx.model.component import Component


__all__ = ["DebHandler"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


class DebHandler(PurlHandler):
    """Class to handle all DEB repository processing."""

    def __init__(self) -> None:
        super().__init__(PurlType.DEB)

        self.repositories: apt_api.Sources | None = None
        self.component_packages: dict[Component, dict[DebPackageData, bool]] = {}

    ####################################################################################################
    # Exported Methods
    ####################################################################################################

    def cache_repositories(self) -> bool:
        """Pull all of the metadata for DEB repositories provided in the config.

        Returns:
            bool: True when any repository was successfully pulled
        """
        if deb_repositories := TypeAdapter(list[DebianRepository]).validate_python(Shares.repositories[self.purl_type]):
            repositories: list[apt_api.Repository] = []
            expected = sum(len(repo.distributions) for repo in deb_repositories)
            Shares.log.info(f"Pulling {expected} DEB repositories...")

            repositories_dir: Final[Path] = self.cache_dir / "repositories"
            repositories_dir.mkdir(parents=True, exist_ok=True)

            architectures = {
                get_component_architecture(component) for component in Shares.purl_components[self.purl_type]
            } - {"all"}  # Components with the all architecture are found in "all" specific architecture repositories

            for repo in deb_repositories:
                for distribution in repo.distributions:
                    auth, verify = http.get_auth_and_verify(repo.credentials, repo.certificate)
                    repositories.extend(
                        apt_api.Repository(
                            repo.url, distribution.name, distribution.components, arch, repositories_dir, auth, verify
                        )
                        for arch in architectures
                    )

            self.repositories = apt_api.Sources(repositories)

            log_repo_pulls(expected, len(repositories), self.purl_type)

        return bool(self.repositories)

    def resolve_component_packages(self) -> None:
        """Resolve all DEB components to the packages in the repositories."""
        Shares.log.info(f"Resolving packages for {len(Shares.purl_components[self.purl_type])} DEB components")
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

            self.component_packages[component] = dict.fromkeys(packages, False)

    def populate_required_components(self, files: set[str]) -> None:
        """Determine which components provide the given files.

        Arguments:
            files: The files to search for in the component packages
        """
        required_packages: set[DebPackageData] = set()

        for file in files:
            file_found = False
            for component in Shares.purl_components[self.purl_type]:
                if any(
                    (Shares.options.keep_essential_os_components and package.is_essential())
                    or package.provides_file(file)
                    for package in self.component_packages[component]
                ):
                    file_found = True
                    if component not in self.required_components:
                        Shares.log.debug(f"Component required: {component.name}-{component.version}")
                        self.required_components.add(component)
                        required_packages.update(self.component_packages[component])
                    break

            if not file_found:
                Shares.log.warning(f"Unable to determine what component provides file: {file}")

        Shares.log.info(f"Found {len(self.required_components)} required DEB components")

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
            Shares.log.debug(f"Getting DEB dependencies for {component.name}-{component.version}")
            amount_before = len(self.dependency_components)
            self._populate_nested_file_dependencies(component)
            Shares.log.debug(f"Found {len(self.dependency_components) - amount_before} new DEB dependencies")

        Shares.log.info(f"Found {len(self.dependency_components) - sbom_dependency_count} DEB dependencies")

        dependency_packages = {
            package for component in self.dependency_components for package in self.component_packages[component]
        }

        with self.cache_dir.joinpath("dependency-packages.txt").open("w", encoding="utf-8") as file:
            file.writelines([f"{pkg}\n" for pkg in sorted(dependency_packages, key=lambda p: p.name)])

    ####################################################################################################
    # Utility Methods
    ####################################################################################################

    def _get_component_packages(self, component: Component) -> set[DebPackageData]:
        packages: set[DebPackageData] = set()
        if self.repositories:
            package_datas: set[DebPackageData] = {DebPackageData(package) for package in self.repositories.packages}
            packages.update({package for package in package_datas if package == component})

        return packages

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
        package_dependencies = {
            dependency
            for package_data in self.component_packages[component]
            for dependency in package_data.package.depends
        }
        unmatched_components = (
            self.component_packages.keys()
            - self.denylist_components
            - (self.allowlist_components | self.required_components | self.dependency_components)
        )

        for package_dependency in package_dependencies:
            for unmatched_component in unmatched_components:
                if any(
                    package.satisfies_dependency(package_dependency)
                    for package in self.component_packages[unmatched_component]
                ) or any(
                    package.satisfies_dependency(alternate)
                    for package in self.component_packages[unmatched_component]
                    for alternate in package_dependency.alternates
                ):
                    self.dependency_components.add(unmatched_component)
                    new_dependencies.add(unmatched_component)

        for dependency in new_dependencies:
            self._populate_nested_sbom_dependencies(dependency)

        for dependency in new_dependencies:
            self._populate_nested_file_dependencies(dependency)
