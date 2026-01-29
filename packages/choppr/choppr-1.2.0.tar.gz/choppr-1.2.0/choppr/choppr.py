"""Choppr refines the components in a Software Bill of Materials (SBOM).

It does not replace SBOM generation tools.  Mainly, Choppr analyses a build or runtime to verify
which components are used, and remove the SBOM components not used.  Starting with file accesses, it
works backwards from how an SBOM generation tool typically would.  For example SBOM generators use
the yum database to determine which packages yum installed.  Choppr looks at all the files accessed
and queries sources like yum to determine the originating package.
"""

from __future__ import annotations

import json
import logging
import re
import shutil

from copy import deepcopy
from threading import Lock, Thread
from typing import TYPE_CHECKING, Any, cast

from cyclonedx.model.component import Component, ComponentScope, ComponentType
from cyclonedx.model.dependency import Dependency
from cyclonedx.output.json import BY_SCHEMA_VERSION
from packageurl import PackageURL
from pydantic import HttpUrl, ValidationError
from pydantic_yaml import parse_yaml_file_as
from rich.console import Console

from choppr import __version__, context
from choppr.component_handlers.deb_handler import DebHandler
from choppr.component_handlers.rpm_handler import RpmHandler
from choppr.types.configuration import Configuration
from choppr.types.enums import PurlType
from choppr.types.shares import Shares
from choppr.utils.components import get_component_dependency, get_purl_type
from choppr.utils.files import compress_directory, extract_archive, output_list, schema_sort_json, version_existing_file
from choppr.utils.logging import log_header


if TYPE_CHECKING:
    from pathlib import Path

    from cyclonedx.model.bom import Bom
    from cyclonedx.model.bom_ref import BomRef
    from sortedcontainers import SortedSet

    from choppr.component_handlers.purl_handler import PurlHandler
    from choppr.types.enums import OperatingMode


__all__ = ["Choppr"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


console = Console(width=120)


def _clear_cache() -> None:
    Shares.log.info("Clearing cache")
    shutil.rmtree(Shares.options.cache_dir)


class Choppr:
    """Implementation of Choppr."""

    def __init__(  # noqa: PLR0913, PLR0917
        self,
        mode: OperatingMode,
        log: logging.Logger,
        config_file: Path,
        input_sbom: Path | None = None,
        input_strace: Path | None = None,
        output_sbom: Path | None = None,
    ) -> None:
        """Initialize plugin with Hoppr framework arguments (context and config).

        Arguments:
            mode: Operating mode to run in
            log: Logger to use
            config_file: The path to the config file
            input_sbom: The path to the SBOM to process and filter the components of
            input_strace: The path to the output file created when running strace on your build or runtime executable
            output_sbom: The path to write the chopped sbom to (default None)

        Raises:
            FileNotFoundError: Raised when the configuration file can't be accessed
            ValidationError: Raised when the provided configuration file is invalid
            ValueError: Raised when the provided configuration file is invalid
        """
        # Configure log
        logging.captureWarnings(True)
        warnings_log = logging.getLogger("py.warnings")
        for handler in log.handlers:
            warnings_log.addHandler(handler)
        warnings_log.setLevel(log.level)
        # Parse configuration
        try:
            context.config_directory = config_file.parent
            context.cli_input_sbom = input_sbom
            context.cli_input_strace = input_strace
            context.cli_output_sbom = output_sbom
            config = parse_yaml_file_as(Configuration, config_file)
            if not context.cli_output_sbom:
                config.output_files.sbom = config.input_files.sbom.parent.joinpath(
                    f"chopped-{config.input_files.sbom.name}"
                )
            Shares(mode, config, log)
        except FileNotFoundError:
            log.error(f"Configuration file not found: {config_file}")  # noqa: TRY400
            raise
        except ValueError as e:
            log.error(f"Invalid configuration: {e}")  # noqa: TRY400
            raise
        except ValidationError:
            log.exception("Invalid configuration")
            raise

        log.info(f"Config File: {config_file.resolve()}")
        log.info(f"Input File - SBOM: {Shares.input_files.sbom.resolve()}")
        if Shares.input_files.strace_results:
            log.info(f"Input File - strace Results: {Shares.input_files.strace_results.resolve()}")
        if Shares.input_files.cache_archive:
            log.info(f"Input File - Cache Archive: {Shares.input_files.cache_archive.resolve()}")
        log.info(f"Output File - SBOM: {Shares.output_files.sbom.resolve()}")

        self.search_repositories = dict.fromkeys(PurlType, False)
        self.preprocessed_files: set[str] = set()
        self.preprocessed_components: set[Component] = set()
        self.purl_handlers: dict[PurlType, PurlHandler] = {PurlType.RPM: RpmHandler(), PurlType.DEB: DebHandler()}
        self.unimplemented_purl_types_logged: set[PurlType] = set()
        self.unimplemented_component_types_logged: set[ComponentType] = set()
        self._lock = Lock()

    def _run_handler_methods_concurrently(
        self,
        method_name: str,
        header: str,
        *args: Any,  # noqa: ANN401
        purl_types: set[PurlType] | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> tuple[list[Thread], dict[PurlType, Any]]:
        if purl_types is None:
            purl_types = set(self.purl_handlers.keys())

        log_header(header)

        results: dict[PurlType, Any] = dict.fromkeys(purl_types)
        threads: list[Thread] = []

        def _run_with_result(handler: PurlHandler, purl_type: PurlType) -> None:
            """Run the method and store its return value."""
            method = getattr(handler, method_name)
            result = method(*args, **kwargs)

            with self._lock:
                results[purl_type] = result

        # Create threads for each handler
        for purl_type in purl_types:
            if purl_type in self.purl_handlers:
                thread = Thread(target=_run_with_result, args=(self.purl_handlers[purl_type], purl_type))
                threads.append(thread)
                thread.start()

        return threads, results

    def _pre_process_components(self) -> None:
        log_header("Pre-Processing Components")

        for file in Shares.strace_files:
            for pattern, component in Shares.pattern_components:
                if re.search(pattern, file):
                    Shares.log.debug(f'File "{file}" provided by {component.name}-{component.version}')
                    self.preprocessed_files.add(file)
                    self.preprocessed_components.add(component)

    def _cache_repositories(self, clear: bool = False) -> None:
        if clear:
            _clear_cache()

        threads, results = self._run_handler_methods_concurrently("cache_repositories", "Cache Repositories")
        for thread in threads:
            thread.join()

        # Update search_repositories with return values
        with self._lock:
            for purl_type, result in results.items():
                if isinstance(result, bool):
                    self.search_repositories[purl_type] = result

    def _resolve_component_packages(self) -> None:
        if purl_types := {pt for pt in self.purl_handlers if self.search_repositories[pt]}:
            threads, _ = self._run_handler_methods_concurrently(
                "resolve_component_packages", "Resolve Component Packages", purl_types=purl_types
            )
            for thread in threads:
                thread.join()

    def _resolve_allowlist_denylist(self) -> None:
        threads, _ = self._run_handler_methods_concurrently(
            "resolve_allowlist_denylist", "Resolving Allowlist and Denylist", purl_types=set(PurlType)
        )
        for thread in threads:
            thread.join()

    def _populate_required_components(self) -> None:
        if purl_types := {pt for pt in self.purl_handlers if self.search_repositories[pt]}:
            required_files = Shares.strace_files - self.preprocessed_files
            threads, _ = self._run_handler_methods_concurrently(
                "populate_required_components", "Populate Required Components", required_files, purl_types=purl_types
            )
            for thread in threads:
                thread.join()

    def _populate_dependency_components(self) -> None:
        if purl_types := {pt for pt in self.purl_handlers if self.search_repositories[pt]}:
            threads, _ = self._run_handler_methods_concurrently(
                "populate_dependency_components", "Populate Dependency Components", purl_types=purl_types
            )
            for thread in threads:
                thread.join()

    def _filter_sbom(self) -> Bom:  # noqa: C901
        log_header("Filter SBOM")
        choppd_sbom = deepcopy(Shares.sbom)
        choppd_sbom.components.clear()
        choppd_sbom.dependencies.clear()
        excluded_components: dict[BomRef, Component] = {}
        components_required = 0
        components_excluded = 0
        components_unknown = 0

        root_dependency = (
            Dependency(choppd_sbom.metadata.component.bom_ref, []) if choppd_sbom.metadata.component else None
        )

        def _require_component(component: Component, is_root_dependency: bool = False) -> None:
            nonlocal choppd_sbom, components_required, root_dependency

            component.scope = ComponentScope.REQUIRED
            choppd_sbom.components.add(component)
            if dependency := get_component_dependency(component):
                choppd_sbom.dependencies.add(dependency)
                if is_root_dependency and root_dependency:
                    root_dependency.dependencies.add(dependency)
            components_required += 1

        def _exclude_component(component: Component) -> None:
            nonlocal components_excluded

            component.scope = ComponentScope.EXCLUDED
            components_excluded += 1

        for component in Shares.sbom.components or []:
            component_id = f"{component.name}-{component.version}"

            # Previously Excluded
            if component.scope == ComponentScope.EXCLUDED:
                Shares.log.debug(f"Component previously excluded: {component_id}")
                components_excluded += 1
                continue

            # Component Parsing
            match component_scope := self._get_component_scope(component):
                case _ if component_scope and component_scope[0] is ComponentScope.REQUIRED:
                    Shares.log.debug(f"Component required: {component_id}")
                    _require_component(component, component_scope[1])
                    continue
                case _ if component_scope and component_scope[0] is ComponentScope.EXCLUDED:
                    Shares.log.debug(f"Component not required: {component_id}")
                    _exclude_component(component)
                    continue

            components_unknown += 1

        if root_dependency:
            choppd_sbom.dependencies.add(root_dependency)

        # Clean Dependencies
        excluded_components = {c.bom_ref: c for c in Shares.sbom.components if c.scope is ComponentScope.EXCLUDED}

        for dependency in choppd_sbom.dependencies:
            clean_dependencies: list[Dependency] = [
                d for d in dependency.dependencies if d.ref not in excluded_components
            ]

            for sub_dependency in dependency.dependencies - clean_dependencies:
                excluded_component = excluded_components[sub_dependency.ref]
                Shares.log.warning(
                    "Required component depends on excluded component: "
                    f"{excluded_component.name}-{excluded_component.version}"
                )

            dependency.dependencies = clean_dependencies

        Shares.log.info(f"Components Required: {components_required}")
        Shares.log.info(f"Components Excluded: {components_excluded}")
        Shares.log.info(f"Components Unknown: {components_unknown}")

        if Shares.options.delete_excluded:
            Shares.log.info("Deleted excluded components")
            return choppd_sbom
        return Shares.sbom

    @staticmethod
    def _output_excluded_components(filtered_components: SortedSet[Component]) -> None:
        excluded_components_all = cast(
            "list[Component]", [c for c in Shares.sbom.components if c not in filtered_components]
        )

        for purl_type in PurlType:
            output_format = Shares.output_files.excluded_components[purl_type].component_format
            if excluded_components := [
                output_format.format(name=c.name, version=c.version)
                for c in excluded_components_all
                if get_purl_type(c) is purl_type
            ]:
                output_file = Shares.output_files.excluded_components[purl_type].file
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_list(output_file, excluded_components)

    @staticmethod
    def _output_sbom(sbom: Bom) -> None:
        Shares.output_files.sbom.parent.mkdir(parents=True, exist_ok=True)
        version_existing_file(Shares.output_files.sbom)

        outputter = BY_SCHEMA_VERSION[Shares.sbom_schema_version](sbom)

        if Shares.options.sort_sbom:
            if schema_url := outputter._get_schema_uri():  # noqa: SLF001
                sbom_data: dict[str, Any] = json.loads(outputter.output_as_string())
                sorted_sbom = schema_sort_json(sbom_data, HttpUrl(schema_url))
                with Shares.output_files.sbom.open("w") as file:
                    json.dump(sorted_sbom, file, indent=2)
                return

            Shares.log.error("Unable to sort SBOM: There is no schema available for the given SBOM version")

        outputter.output_to_file(str(Shares.output_files.sbom), True, indent=2)

    def _get_component_scope(self, component: Component) -> tuple[ComponentScope, bool] | None:
        # Allowlist/Denylist
        if scope := self._get_allowlist_denylist_scope(component):
            return scope, scope is ComponentScope.REQUIRED

        # Pre-Processed Components
        if component in self.preprocessed_components:
            return ComponentScope.REQUIRED, True

        # Processed Components
        if (Shares.options.allow_version_mismatch or component.version) and (
            (
                root_component := (
                    component in self._get_purl_required_components() or self._is_required_file_component(component)
                )
            )
            or component in self._get_purl_dependency_components()
        ):
            return ComponentScope.REQUIRED, root_component

        if component.type == ComponentType.OPERATING_SYSTEM:
            return (
                (ComponentScope.REQUIRED, False)
                if Shares.options.keep_essential_os_components
                else (ComponentScope.EXCLUDED, False)
            )

        if (purl_type := get_purl_type(component)) in self.purl_handlers:
            return ComponentScope.EXCLUDED, False

        if purl_type and purl_type not in self.unimplemented_purl_types_logged:
            self.unimplemented_purl_types_logged.add(purl_type)
            Shares.log.debug(f"Purl support not implemented yet: {purl_type}")
        elif not purl_type and component.type not in self.unimplemented_component_types_logged:
            self.unimplemented_component_types_logged.add(component.type)
            Shares.log.debug(f"Component support not implemented yet: {component.type}")

        return None

    def _get_allowlist_denylist_scope(self, component: Component) -> ComponentScope | None:
        if component in self._get_purl_allowlist_components():
            return ComponentScope.REQUIRED
        if component in self._get_purl_denylist_components():
            return ComponentScope.EXCLUDED

        return None

    def _get_purl_allowlist_components(self) -> set[Component]:
        return {component for handler in self.purl_handlers.values() for component in handler.allowlist_components}

    def _get_purl_denylist_components(self) -> set[Component]:
        return {component for handler in self.purl_handlers.values() for component in handler.denylist_components}

    def _get_purl_required_components(self) -> set[Component]:
        return {component for handler in self.purl_handlers.values() for component in handler.required_components}

    def _get_purl_dependency_components(self) -> set[Component]:
        return {component for handler in self.purl_handlers.values() for component in handler.dependency_components}

    @classmethod
    def _is_required_file_component(cls, component: Component) -> bool:
        return component.type == ComponentType.FILE and component.name in Shares.strace_files

    @classmethod
    def _archive_cache(cls) -> None:
        Shares.log.info("Creating cache archive...")
        compress_directory(Shares.output_files.cache_archive, Shares.options.cache_dir)
        Shares.log.info(f"Cache archive written to {Shares.output_files.cache_archive}")

    def run(self) -> bool:
        """Execute Choppr in run mode.

        Returns:
            bool: Return True if Choppr ran successfully
        """
        if Shares.input_files.cache_archive:  # Extract provided cache
            extract_archive(Shares.input_files.cache_archive, Shares.options.cache_dir)
        self._pre_process_components()
        self._cache_repositories()
        self._resolve_component_packages()
        self._resolve_allowlist_denylist()
        self._populate_required_components()
        self._populate_dependency_components()

        choppd_sbom = self._filter_sbom()

        choppd_sbom.metadata.tools.components.add(
            Component(
                name="choppr",
                type=ComponentType.APPLICATION,
                bom_ref=f"pkg:pypi/choppr@{__version__}",
                version=__version__,
                scope=ComponentScope.EXCLUDED,
                purl=PackageURL(type="pypi", name="choppr", version=__version__),
            )
        )

        self._output_excluded_components(choppd_sbom.components)
        self._output_sbom(choppd_sbom)

        if Shares.options.archive_cache:
            self._archive_cache()

        if Shares.options.clear_cache:
            _clear_cache()

        return True

    def cache(self) -> bool:
        """Execute Choppr in cache mode.

        Returns:
            bool: Return True if Choppr ran successfully
        """
        self._cache_repositories(True)
        self._archive_cache()

        if Shares.options.clear_cache:
            _clear_cache()

        return True
