"""Utility functions used to process SBOM components."""

from __future__ import annotations

import contextlib
import re

from typing import TYPE_CHECKING

from choppr.types.enums import PurlType
from choppr.types.shares import Shares


if TYPE_CHECKING:
    from cyclonedx.model.bom_ref import BomRef
    from cyclonedx.model.component import Component
    from cyclonedx.model.dependency import Dependency


__all__ = [
    "get_component_architecture",
    "get_component_dependencies",
    "get_component_dependency",
    "get_component_from_ref",
    "get_purl_type",
]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


def get_component_architecture(component: Component) -> str:
    """Get the architecture of the given component, if it has one.

    Arguments:
        component: The component to get the architecture of

    Returns:
        str: The architecture, if it is defined, else, "noarch"
    """
    if match := re.search(r"\?.*(?:arch=(?P<architecture>.+?)(?:&|$))", str(component.bom_ref)):
        return match["architecture"]

    return "noarch"


def get_component_dependencies(component: Component) -> set[Component]:
    """Check if the given component is in the dependencies section of an SBOM.

    Arguments:
        component: The component to get the dependencies of

    Returns:
        set[Component]: The list of dependencies for a component
    """
    dependencies: set[Component] = set()

    if dependency := get_component_dependency(component):
        dependencies.update(
            ref_component
            for ref in (dependency.dependencies_as_bom_refs() or [])
            if (ref_component := get_component_from_ref(ref))
        )

    return dependencies


def get_component_dependency(component: Component) -> Dependency | None:
    """Get the dependency associated with the given component.

    Arguments:
        component: The component to get the dependency of

    Returns:
        Dependency | None: The dependency if it exists
    """
    return (
        next((d for d in Shares.sbom.dependencies if d.ref == component.bom_ref), None)
        if Shares.sbom.dependencies
        else None
    )


def get_component_from_ref(ref: BomRef) -> Component | None:
    """Get the component from the SBOM that has a bom_ref that matches the given ref.

    Arguments:
        ref: The ref to search for

    Returns:
        Component | None: The component matching the given ref
    """
    return next((c for c in Shares.sbom.components if c.bom_ref == ref), None)


def get_purl_type(component: Component) -> PurlType | None:
    """Get the purl type for the provided component.

    Arguments:
        component: SBOM component

    Returns:
        PurlType | None: The purl type for the component
    """
    if component.purl and (match := re.match(r"pkg:(?P<type>.*?)/", component.purl.to_string())):
        with contextlib.suppress(KeyError):
            return PurlType(match["type"].upper())
    return None
