"""Module for the enumerations used in Choppr."""

from __future__ import annotations

from enum import Enum


__all__ = ["OperatingMode", "PurlType"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


class OperatingMode(str, Enum):
    """Modes to change the behavior of Choppr."""

    RUN = "run"
    """Run choppr normally, and filter the SBOM"""
    CACHE = "cache"
    """Only create the cache for Choppr, and export it as an archive."""


class PurlType(str, Enum):
    """Enumeration of supported purl types."""

    ALPM = "alpm"
    APK = "apk"
    BITBUCKET = "bitbucket"
    BITNAMI = "bitnami"
    CARGO = "cargo"
    COCOAPODS = "cocoapods"
    COMPOSER = "composer"
    CONAN = "conan"
    CONDA = "conda"
    CPAN = "cpan"
    CRAN = "cran"
    DEB = "deb"
    DOCKER = "docker"
    GEM = "gem"
    GENERIC = "generic"
    GITHUB = "github"
    GITLAB = "gitlab"
    GOLANG = "golang"
    HACKAGE = "hackage"
    HEX = "hex"
    HUGGINGFACE = "huggingface"
    LUAROCKS = "luarocks"
    MAVEN = "maven"
    MLFLOW = "mlflow"
    NPM = "npm"
    NUGET = "nuget"
    OCI = "oci"
    PUB = "pub"
    PYPI = "pypi"
    QPKG = "qpkg"
    RPM = "rpm"
    SWID = "swid"
    SWIFT = "swift"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def _missing_(cls, value: object) -> PurlType | None:
        return next((member for member in cls if member.value == str(value).lower()), None)
