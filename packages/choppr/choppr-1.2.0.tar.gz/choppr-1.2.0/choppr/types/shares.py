"""Class definition for ChopprShares, a singleton class to share commonly access objects."""

from __future__ import annotations

import json
import re

from typing import TYPE_CHECKING, Any, cast

from cyclonedx.model.bom import Bom
from cyclonedx.model.component import ComponentType
from cyclonedx.schema.schema import SCHEMA_VERSIONS

from choppr import strace
from choppr.types.enums import OperatingMode, PurlType


if TYPE_CHECKING:
    from logging import Logger

    from cyclonedx.model.component import Component
    from typing_extensions import Self

    from choppr.types.configuration import Configuration


__all__ = ["Shares"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2024 Lockheed Martin Corporation"
__license__ = "MIT License"


def _has_choppr_pattern(component: Component) -> bool:
    return "choppr-pattern" in {prop.name for prop in component.properties}


def _get_choppr_pattern(component: Component) -> re.Pattern[str] | None:
    choppr_pattern = next(
        (prop.value for prop in component.properties if prop.name == "choppr-pattern"),
        None,
    )
    return re.compile(choppr_pattern) if choppr_pattern else None


class Shares:
    """Singleton class to hold commonly accessed Choppr objects."""

    _instance: Self | None = None

    def __new__(cls, mode: OperatingMode, config: Configuration, log: Logger) -> Self:
        """Initialize ChopprShares singleton.

        Arguments:
            mode: The operating mode to run Choppr in
            config: Instance of Configuration
            log: Instance of Logger

        Raises:
            ValueError: Raised when the configuration is invalid

        Returns:
            Self: Singleton instance of ChopprShares
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)

            cls.mode = mode
            cls.input_files = config.input_files
            cls.options = config.options
            cls.output_files = config.output_files
            cls.repositories = config.repositories
            cls.log: Logger = log

            cls.options.cache_dir.mkdir(parents=True, exist_ok=True)

            if cls.mode is OperatingMode.RUN and cls.input_files.strace_results is None:
                raise ValueError("Invalid configuration: 'strace_results' is required in run mode")

            cls.strace_files = cls._parse_strace_results()

            with cls.options.cache_dir.joinpath("filtered-strace-results.txt").open("w", encoding="utf-8") as output:
                output.writelines([f"{file}\n" for file in cls.strace_files])

            with cls.input_files.sbom.open("r", encoding="utf-8") as sbom_file:
                sbom_data = cast("dict[str, Any]", json.load(sbom_file))
                cls.sbom_schema_version, cls.sbom_schema = next(
                    (version, schema)
                    for version, schema in SCHEMA_VERSIONS.items()
                    if version.to_version() == sbom_data.get("specVersion")
                )
                cls.sbom: Bom = Bom.from_json(sbom_data)  # type: ignore[attr-defined]

            cls.pattern_components: set[tuple[re.Pattern[str], Component]] = {
                (pattern, component)
                for component in cls.sbom.components
                if _has_choppr_pattern(component) and (pattern := _get_choppr_pattern(component)) is not None
            }
            cls.purl_components: dict[PurlType, list[Component]] = {
                purl_type: [
                    component
                    for component in cls.sbom.components
                    if component.purl and component.purl.type == purl_type.value.lower()
                ]
                for purl_type in PurlType
            }
            cls.file_components: set[Component] = {
                component for component in cls.sbom.components if component.type is ComponentType.FILE
            }

            cls.log.debug("Purl component counts:")
            for purl_type, component_list in cls.purl_components.items():
                if component_count := len(component_list):
                    cls.log.debug(f"    {purl_type.name}: {component_count}")
            cls.log.debug(f"File component count: {len(cls.file_components)}")
        return cls._instance

    @classmethod
    def initialized(cls) -> bool:
        """Check if the class has been initialized.

        Returns:
            bool: True if the class is initialized, otherwise False
        """
        return cls._instance is not None

    @classmethod
    def _parse_strace_results(cls) -> set[str]:
        parsed_strace_files: set[str] = set()

        if cls.input_files.strace_results:
            parsed_strace_files = strace.get_files(cls.input_files.strace_results)

            if cls.options.strace_regex_excludes:
                parsed_strace_files = {
                    file
                    for file in parsed_strace_files
                    if not any(bool(re.search(exclude, str(file))) for exclude in cls.options.strace_regex_excludes)
                }

        return parsed_strace_files
