"""Model for the configuration for Choppr."""

from __future__ import annotations

import os
import re

from datetime import timedelta
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any

from cyclonedx.model.component import Component
from pydantic import (  # noqa: TC002
    AfterValidator,
    BaseModel,
    BeforeValidator,
    Field,
    HttpUrl,
    PositiveFloat,
    PositiveInt,
    PrivateAttr,
    SecretStr,
    field_validator,
    model_validator,
)

from choppr import context
from choppr.constants import (
    ARCHIVE_EXTENSIONS,
    COMPONENT_LIST_FORMATS,
    DEFAULT_RECURSION_LIMIT,
    PLACEHOLDER_REPOSITORY_URL,
)
from choppr.types.enums import PurlType
from choppr.utils.files import version_existing_file


if TYPE_CHECKING:
    from typing_extensions import Self


__all__ = ["Configuration", "Credentials", "DebianRepository", "Repository"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


########################################################################################################################
# Validators
########################################################################################################################


def _validate_file_path(value: Path) -> Path:
    """Ensure the provided path is a file.

    Arguments:
        value: The path to check

    Raises:
        ValueError: Raised when the file does not exist

    Returns:
        Path: The path, if it exists
    """
    if not value.is_file():
        if context.config_directory.joinpath(value).is_file():
            return context.config_directory.joinpath(value)
        raise ValueError(f"File does not exist: {value}")
    return value


def _normalize_http_url(value: HttpUrl) -> HttpUrl:
    """Remove a trailing slash from the URL.

    Arguments:
        value: The url to normalize

    Returns:
        HttpUrl: The normalized URL
    """
    return HttpUrl(str(value).rstrip("/"))


def _validate_regex(value: str) -> re.Pattern[str]:
    """Ensure the given string is a valid regular expression.

    Arguments:
        value: The string to compile into a regex

    Raises:
        ValueError: Raised when the string is an invalid regular expression

    Returns:
        re.Pattern[str]: The compiled regular expression
    """
    try:
        return re.compile(value)
    except re.error as e:
        raise ValueError(f"Invalid regular expression: {value}") from e


def _get_env_value(variable: str) -> str:
    """Get the value of the provided environment variable.

    Arguments:
        variable: The environment variable key

    Raises:
        ValueError: Raised if the value of environment variable is an empty string

    Returns:
        str: The value of the environment variable
    """
    if value := os.environ[variable]:
        return value
    raise ValueError(variable)


def _validate_archive_path(value: Path) -> Path:
    """Ensure the provided path is a supported archive.

    Arguments:
        value: The path to an archive

    Raises:
        ValueError: Raised if the file extension is not a valid archive type

    Returns:
        Path: The validated archive path
    """
    if value.suffix in ARCHIVE_EXTENSIONS:
        return _validate_file_path(value)
    raise ValueError(f"Invalid archive: {value} - Accepted extensions: {', '.join(ARCHIVE_EXTENSIONS)}")


########################################################################################################################
# Default Values
########################################################################################################################


def _default_repositories() -> dict[PurlType, list[Repository]]:
    return {purl_type: [] for purl_type in PurlType}


def _default_excluded_components() -> dict[PurlType, ExcludedComponentsFile]:
    return {
        purl_type: ExcludedComponentsFile(
            file=Path(f"choppr-excluded-components-{purl_type.name.lower()}.txt"),
            component_format=COMPONENT_LIST_FORMATS.get(purl_type, "{name}={version}"),
        )
        for purl_type in PurlType
    }


########################################################################################################################
# Models
########################################################################################################################


class InputFiles(BaseModel):
    """Class with values for the input files for Choppr."""

    # Required
    sbom: Annotated[Path, AfterValidator(_validate_file_path)]
    # Conditional
    strace_results: Annotated[Path, AfterValidator(_validate_file_path)] | None = None
    # Optional
    cache_archive: Annotated[Path, AfterValidator(_validate_archive_path)] | None = None


class Credentials(BaseModel):
    """Credentials used to access URLs."""

    user_env: str | None = None
    pass_env: str | None
    user: str | None = None
    username: str
    password: SecretStr | None = Field(None, exclude=True)

    @model_validator(mode="before")
    @classmethod
    def validate_credential_required_service(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Dynamically parse credentials using specified environment variables.

        Arguments:
            values: The values for the members of Credentials

        Raises:
            ValueError: Raised if user_env or pass_env are invalid

        Returns:
            dict[str, Any]: The model values with username and/or password set by the environment variables
        """
        try:
            if user := values.get("user"):
                values["username"] = user

            if (user_env := values.get("user_env")) is not None:
                values["username"] = _get_env_value(user_env)

            if (pass_env := values.get("pass_env")) is not None:
                values["password"] = SecretStr(_get_env_value(pass_env))
        except KeyError as ex:
            raise ValueError(f"The environment variable {ex} does not exist") from ex
        except ValueError as ex:
            raise ValueError(f"The environment variable {ex} must be set with a non-empty string") from ex

        return values


class Repository(BaseModel):
    """Class representation for a standard repository."""

    url: Annotated[HttpUrl, AfterValidator(_normalize_http_url)] = PLACEHOLDER_REPOSITORY_URL
    urls: set[Annotated[HttpUrl, AfterValidator(_normalize_http_url)]] | None = None
    credentials: Credentials | None = None
    certificate: Annotated[Path, AfterValidator(_validate_file_path)] | None = None

    @model_validator(mode="after")
    def _validate_url(self) -> Self:
        if not self.url and not self.urls:
            raise ValueError("A URL must be provided for a repository via url or urls")

        return self

    def __hash__(self) -> int:
        return hash(self.url)


class DebianDistribution(BaseModel):
    """Class representation for a debian distribution, to include its name and components."""

    name: str
    components: list[str] = ["main", "restricted", "universe", "multiverse"]


class DebianRepository(Repository):
    """Class representation for a debian repository, to include its URL and distributions."""

    distributions: list[DebianDistribution]


class ExcludedComponentsFile(BaseModel):
    """The filename to output excluded components to, and what format to write them as."""

    file: Path
    component_format: str = ""


class OutputFiles(BaseModel):
    """Class with values for the output files for Choppr."""

    cache_archive: Annotated[Path, AfterValidator(_validate_archive_path)] = Field(
        default_factory=lambda: Path.cwd() / "choppr-cache.tar.gz"
    )
    excluded_components: dict[PurlType, ExcludedComponentsFile] = Field(default_factory=_default_excluded_components)
    sbom: Annotated[Path, AfterValidator(version_existing_file)] = Path("chopped-sbom.cdx.json")

    @field_validator("excluded_components", mode="before")
    @classmethod
    def _validate_excluded_components(cls, value: dict[str, dict[str, str]]) -> dict[PurlType, ExcludedComponentsFile]:
        excluded_components: dict[PurlType, ExcludedComponentsFile] = _default_excluded_components()
        try:
            for purl, file_and_format in value.items():
                purl_type = PurlType[purl.upper()]
                excluded_components_file = ExcludedComponentsFile.model_validate(file_and_format)
                excluded_components[purl_type].file = excluded_components_file.file
                if excluded_components_file.component_format:
                    excluded_components[purl_type].component_format = excluded_components_file.component_format
        except KeyError as e:
            raise ValueError(
                f"Invalid purl type: {e} - Accpeted values: [{', '.join(m.name for m in PurlType)}]"
            ) from e
        else:
            return excluded_components


class HttpRequestLimits(BaseModel):
    """Class with values to configure HTTP request limits."""

    retries: PositiveInt = 3
    retry_interval: PositiveFloat = 5.0
    timeout: PositiveFloat = 60.0


class PackagePattern(BaseModel):
    """Class with the name, version, and purl type for a package."""

    name: Annotated[re.Pattern[str], AfterValidator(_validate_regex)]
    version: Annotated[re.Pattern[str], AfterValidator(_validate_regex)]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PackagePattern):
            return self.name == other.name and self.version == other.version
        if isinstance(other, Component):
            return bool(
                self.name.match(other.name)
                and (
                    (other.version is None and self.version.match(""))
                    or (other.version and self.version.match(other.version))
                )
            )
        return False

    def __hash__(self) -> int:
        sha = sha256()
        sha.update(str(self.name).encode())
        sha.update(str(self.version).encode())
        return int(sha.hexdigest(), 16)


class Options(BaseModel):
    """Class to validate and parse the configuration values provided to ChopprPlugin."""

    HttpRequestLimits.model_rebuild()

    # Optional Attributes
    allow_partial_filename_match: bool = False
    allow_version_mismatch: bool = False
    allowlist: dict[PurlType, set[PackagePattern]] = Field(default={})
    archive_cache: bool = False
    cache_dir: Path = Field(default_factory=lambda: Path.cwd() / ".cache" / "choppr")
    cache_timeout: timedelta | bool = Field(default=timedelta(days=7))
    clear_cache: bool = False
    delete_excluded: bool = True
    denylist: dict[PurlType, set[PackagePattern]] = Field(default={})
    http_limits: HttpRequestLimits = Field(default=HttpRequestLimits())
    keep_essential_os_components: bool = False
    recursion_limit: PositiveInt = DEFAULT_RECURSION_LIMIT
    sort_sbom: bool = False
    strace_regex_excludes: list[Annotated[re.Pattern[str], BeforeValidator(_validate_regex)]] = Field(default=[])
    # Private Attributes
    _strace_files: set[str] = PrivateAttr(default=set())

    @field_validator("cache_timeout", mode="before")
    @classmethod
    def _validate_cache_timeout(cls, cache_timeout: str) -> timedelta | bool:
        timedelta_pattern = re.compile(r"^(?P<duration>\d+)\s?(?P<unit>d|h|m|s)$", re.IGNORECASE)
        boolean_pattern = re.compile(r"^(?P<true>true)|(?P<false>false)$", re.IGNORECASE)

        timeout_match = timedelta_pattern.match(cache_timeout)
        boolean_match = boolean_pattern.match(cache_timeout)

        error_message = "Invalid 'cache_timeout' value: Expected a number followed by a unit (d, h, m, s) or boolean"

        if not (timeout_match or boolean_match):
            raise ValueError(error_message)

        if boolean_match:
            return False if boolean_match["false"] else timedelta()

        timeout_duration = int(timeout_match["duration"])  # type: ignore[index]
        timeout_unit = timeout_match["unit"].lower()  # type: ignore[index]

        unit_map = {
            "d": "days",
            "h": "hours",
            "m": "minutes",
            "s": "seconds",
        }

        if timeout_unit not in unit_map:
            raise ValueError(error_message)

        return timedelta(**{unit_map[timeout_unit]: timeout_duration})

    @field_validator("allowlist", "denylist", mode="before")
    @classmethod
    def _validate_exception_list(cls, value: dict[str, set[PackagePattern]]) -> dict[PurlType, set[PackagePattern]]:
        try:
            return {PurlType[purl_type.upper()]: packages for purl_type, packages in value.items()}
        except KeyError as e:
            raise ValueError(
                f"Invalid purl type: {e} - Accpeted values: [{', '.join(m.name for m in PurlType)}]"
            ) from e

    @model_validator(mode="after")
    def _validate_exception_overlap(self) -> Self:
        for purl_type in PurlType:
            if self.allowlist.get(purl_type, set()) & self.denylist.get(purl_type, set()):
                raise ValueError(f"The allowlist and denylist have at least one overlapping {purl_type.name} package")

        return self


class Configuration(BaseModel):
    """Class with values for Choppr configuration."""

    _config_directory: Path

    input_files: InputFiles
    repositories: dict[PurlType, list[Repository | DebianRepository]] = Field(default_factory=_default_repositories)
    output_files: OutputFiles = Field(default_factory=OutputFiles)
    options: Options = Field(default_factory=Options)

    @model_validator(mode="before")
    @classmethod
    def _cli_overrides(cls, values: dict[str, Any]) -> dict[str, Any]:
        # Override input_files
        input_files: dict[str, Any] = values.get("input_files", {})

        if context.cli_input_sbom:
            input_files["sbom"] = context.cli_input_sbom
        if context.cli_input_strace:
            input_files["strace_results"] = context.cli_input_strace

        values["input_files"] = input_files

        # Override output files
        output_files: dict[str, Any] = values.get("output_files", {})

        if context.cli_output_sbom:
            output_files["sbom"] = context.cli_output_sbom

        values["output_files"] = output_files

        return values

    @field_validator("repositories", mode="after")
    @classmethod
    def _validate_repositories(
        cls, value: dict[PurlType, list[Repository | DebianRepository]]
    ) -> dict[PurlType, list[Repository | DebianRepository]]:
        # Ensure all purl types are associated with a list, even if it's empty
        for purl_type in [pt for pt in PurlType if pt not in value]:
            value[purl_type] = []

        for purl_type, repoitories in value.items():
            expanded_repositories: set[Repository | DebianRepository] = set()
            for repo in repoitories:
                if repo.url is not PLACEHOLDER_REPOSITORY_URL:
                    expanded_repositories.add(repo.model_copy(update={"urls": None}, deep=True))
                if repo.urls:
                    expanded_repositories.update(
                        repo.model_copy(update={"url": url, "urls": None}, deep=True) for url in repo.urls
                    )
            value[purl_type] = list(expanded_repositories)
        return value
