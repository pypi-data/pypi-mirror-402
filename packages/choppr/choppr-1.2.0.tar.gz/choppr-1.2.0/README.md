<div align="center">
  <img src="https://gitlab.com/hoppr/choppr/-/raw/dev/assets/media/choppr_the_crocodile.svg" width="500"/>
</div>

# Choppr

Choppr is a CLI tool to filter unused components out of an SBOM using strace results.

Choppr refines the components in a
[Software Bill of Materials (SBOM)](https://en.wikipedia.org/wiki/Software_supply_chain). It does not replace SBOM
generation tools. Mainly, Choppr analyses a build or runtime to verify which components are used, and remove the SBOM
components not used. Starting with file accesses, it works backwards from how an SBOM generation tool typically would.
For example SBOM generators use the yum database to determine which packages yum installed. Choppr looks at all the
files accessed and queries sources like yum to determine the originating package.

Other intended results include:
- Reducing installed components. Size is optimized. The number of vulnerabilities is reduced. The less tools available
  to an attacker the better.
- Creating a runtime container from the build container
- Detecting files without corresponding SBOM components

## Approaches

How to use Choppr depends on your project and needs. Consider the following use cases and their recommended approaches.

<details><summary><b>Build an SBOM of a software product</b></summary>

The user provides the required content. Choppr determines which components were used during the build. The exclude
list tells Choppr to remove components like CMake, because the user is certain no CMake software was built into their
product. An list of unused packages is generated that can be used to automate removal. Building again after removing
these components verifies no required components were lost.

</details>

<details><summary><b>Create a runtime image and runtime SBOM from a build image</b></summary>

Choppr uses a multistage build to `ADD` the files used. Optionally metadata such as the yum database can be kept. The
additional include list can be used to specify dynamically linked libraries, necessary services, or any other necessary
components that were not exercised during build. This will also be reflected in the SBOM components.

</details>

<details><summary><b>Create a runtime SBOM from a runtime image</b></summary>

Similar to analyzing a build, Choppr can analyze a runtime.

*If this is used to describe a delivery, it should be merged with the Build SBOM.*

</details>
</br>

References:
- [CISA defined SBOM types](https://www.cisa.gov/sites/default/files/2023-04/sbom-types-document-508c.pdf).

## Installation

```sh
pip install choppr
```

## Usage

```sh
Usage: choppr [OPTIONS] OPERATING_MODE:{run|cache}

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ *    operating_mode      OPERATING_MODE:{run|cache}  The operating mode to use [required]                            │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --config          -f      FILE  The configuration file to use [default: choppr.yml]                                  │
│ --input-sbom      -i      FILE  The SBOM to process and filter the components of                                     │
│ --strace-results  -s      FILE  The output file created when running strace on your build or runtime executable      │
│ --output-sbom     -o      FILE  The file to write the chopped SBOM to                                                │
│ --log             -l      FILE  The log file to write to [default: choppr.log]                                       │
│ --verbose         -v            Enable debug logging                                                                 │
│ --version                                                                                                            │
│ --help                          Show this message and exit.                                                          │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

## Configuration

The default path choppr will look for the configuration is `choppr.yml` in the current working directory.

<details>
  <summary>Example Configuration</summary>

```yml
---

input_files:
  sbom: ffmpeg.cdx.json
  strace_results: ffmpeg-strace.txt

repositories:
  rpm:
    - url: https://rocky-linux-us-west4.production.gcp.mirrors.ctrliq.cloud/pub/rocky/8.10/AppStream/x86_64/os/
    - url: http://mirror.siena.edu/rocky/8.10/BaseOS/x86_64/os/
    - url: https://mirrors.iu13.net/rocky/8.10/extras/x86_64/os/

options:
  strace_regex_excludes:
    - ^.*ffmpeg.*$
    - ^.*\.(c|cpp|cxx|h|hpp|o|py|s)$
    - ^/usr/share/pkgconfig$
    - ^/tmp$
    - ^bin$
    - ^.*\.git.*$
    - ^.*(\.\.)+.*$
    - ^.*(CMakeFiles.*|\.cmake)$
```

</details>

### Variables

```yml
input_files:
  sbom: Path
  strace_results: Path | None
  cache_archive: Path | None

repositories:  # dict[PurlType, list[Repository]]
  _purl_type_:  # PurlType
    - url: HttpUrl | None
      urls:  # list[HttpUrl] | None
        - ...
      credentials:  # Credentials | None
        username: str | None
        user_env: str | None
        pass_env: str | None
      certificate: Path | None
    ...
  deb: # Debian repositories have extra configuration beyond the standard configuration above
    - url: ...
      credentials: ...
      certificate: ...
      distributions:
        - name: str
          components:  # list[str]
            - main
            - security

output_files:  # OutputFiles | None
  cache_archive: Path | None
  excluded_components: # dict[PurlType, ExcludedPackageFile] | None
    _purl_type_: # PurlType
      file: Path
      component_format: str | None
    ...
  sbom: Path | None

options:
  allow_partial_filename_match: bool
  allow_version_mismatch: bool
  allowlist:  # dict[PurlType, PackagePattern]
    _purl_type_:  # PurlType
      - name: regex
        version: regex
  archive_cache: bool
  cache_dir: Path
  cache_timeout: timedelta | bool
  clear_cache: bool
  delete_excluded: bool
  denylist:  # dict[PurlType, PackagePattern]
    _purl_type_:  # PurlType
      - name: regex
        version: regex
  http_limits:
    retries: PositiveInt
    retry_interval: PositiveFloat
    timeout: PositiveFloat
  keep_essential_os_components: bool
  recursion_limit: PositiveInt
  sort_sbom: bool
  strace_regex_excludes: list[regex]
```

### Common Types

<details>
  <summary><b>PurlType</b></summary>

The purl type, as defined in the package URL [specification](https://github.com/package-url/purl-spec).

The list of available options can be found
[here](https://github.com/package-url/purl-spec/blob/main/purl-types-index.json).

**Type:** `str`

</details>

### Input Files

<details>
  <summary><b>sbom</b></summary>

The SBOM to process and filter the components of with Choppr.

This file is expected to be a JSON file in the [CycloneDX](https://cyclonedx.org/) format.

**Type:** `Path`

**Example Usage:**
```yml
imput_files:
  sbom: my-awesome-sbom.cdx.json
```

</details>

<details>
  <summary><b>strace_results</b></summary>

The path to the output file created when running strace on your build or runtime executable.

This must be provided when `operating_mode` is set to `run`.

This file can be creating using the following command to wrap your build script or runtime executable. The `strace` tool
must be installed on your system separately from choppr.

```sh
strace -f -e trace=file -o "strace_output.txt" <build script/runtime executable>
```

**Type:** `Path | None`

**Default:** `None`

**Example Usage:**
```yml
input_files:
  strace_results: strace_output.txt
```

</details>

<details>
  <summary><b>cache_archive</b></summary>

The path for the cache archive to load to avoid pulling cache data again, or when offline.

**Type:** `Path | None`

**Default:** `None`

**Example Usage:**
```yml
input_files:
  cache_archive: /backup/choppr-cache.tar.gz
```

</details>

### Repositories

**Type:** `dict[PurlType, list[Repository]]`


To obtain the list of repositories on your system, use one of the following commands:

```sh
# For RHEL 8 and later
dnf repolist --verbose

# For RHEL 7 and earlier
yum repolist --verbose

# For Debian
cat /etc/apt/sources.list /etc/apt/sources.list.d/*
```

With the output from one of these commands, you should be able to find the URLs to the repositories used on your system.

<details>
  <summary><b>Repository</b></summary>

The URL for a repository, or multiple repository URLs, paired with optional credentials and/or a certificate.

Debian repositories have an extra distributions keyword.

**Type:**
```yml
# You must provide a url or a list of urls using one or both of the following keys
url: HttpUrl | None
urls: list[HttpUrl] | None
credentials: Credentials | None
certificate: Path | None
# Debian ONLY
distributions: list[DebianDistribution]
```

**Example Usage:**
```yml
repositories:
  rpm:
    - url: http://public.repo.com
    - url: http://private.repo.com
      credentials:
        username: repouser
        pass_env: PRIVATE_REPO_PASSWORD
      certificate: /my/private/repo/cert.pem
    - urls:
        - http://private.repo.com/base
        - http://private.repo.com/updates
        - http://private.repo.com/security
      credentials:
        username: repouser
        pass_env: PRIVATE_REPO_PASSWORD
    ...
  deb:
    - url: http://archive.ubuntu.com/ubuntu
      distributions:
        - name: jammy
          components:
            - main
            - security
            ...
        ...
    ...
  ...
```

</details>

<details>
  <summary><b>Credentials</b></summary>

The credentials to use when accessing the repository.

If you provide `user_env`, it will override the value of username.  You only need to provide one or the other.

**Type:**
```yml
username: str
user_env: str
pass_env: str
```

</details>

<details>
  <summary><b>DebianDistribution</b></summary>

Distribution information for a Debian repository.

**Type:**
```yml
name: str
components: list[str]
```

**Default:**
```yml
name:  # This is required, and has no default
components:
  - main
  - restricted
  - universe
  - multiverse
```

</details>

### Output Files

<details>
  <summary><b>cache_archive</b></summary>

The path to write the cache archive to that can be used later as an input.

**Type:** `Path | None`

**Default:** `None`

**Example Usage:**
```yml
output_files:
  cache_archive: /backup/choppr-cache.tar.gz
```

</details>

<details>
  <summary><b>excluded_components</b></summary>

The paths to write excluded components to using the optionally provided format when writing components to the list.

**Type:** `dict[PurlType, ExcludedComponentsFile]`

**Default:**
```yml
_purl_type_:
  file: "choppr-excluded-components-<purl_type>.txt"
  component_format: "<excluded_component_format>"
...
```

For `excluded_component_format` the default value is `{name}={version}` except for NPM, and RPM. Those are as follows:
```yml
NPM: "{name}@{version}"
RPM: "{name}-{version}"
```

**Example Usage:**
```yml
output_files:
  excluded_components:
    deb:
      file: excluded_deb_components.csv
      component_format: "{name},{version}
```

</details>

<details>
  <summary><b>sbom</b></summary>

The path to write the chopped SBOM to.

By default it outputs to the same folder as the input sbom, using the same filename, with chopped prepended.

**Type:** `Path`

**Default:** `chopped-<input_sbom>`

**Example Usage:**
```yml
output_files:
  sbom: chopped-sbom.cdx.json
```

</details>

### Options

<details>
  <summary><b>allow_partial_filename_match</b></summary>

Allow partial matching for filenames when comparing strace files to files provided by remote repository packages.

This may be useful when symlinks are used for libraries. This is currently only implemented for RPMs.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  allow_partial_filename_match: true
```

</details>

<details>
  <summary><b>allow_version_mismatch</b></summary>

Allow version numbers to be mismatched when comparing SBOM packages to remote repository packages.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  allow_version_mismatch: true
```

</details>

<details>
  <summary><b>allowlist</b></summary>

A dictionary with packages to always keep in the SBOM.

The keys are purl types, and the values are a list of packages. A package has two members, name and version, both are
regex patterns.

**Type:**
```yml
allowlist: # dict[PurlType, list[PackagePattern]]
  _purl_type_: # str (deb, npm, rpm, ...)
    - name: regex
      version: regex
    ...
  ...
```

**Default:** `{}`

**Example Usage:**
```yml
options:
  allowlist:
    deb:
      - name: ".*"
        version: ".*"
    generic:
      - name: "^python$"
        version: "^3.10"
```

</details>

<details>
  <summary><b>archive_cache</b></summary>

Enable `archive_cache` to archive the cache directory when Choppr finishes running in `run` mode.

This has no effect in `cache` mode, as the archive will always be created in that mode.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  archive_cache: true
```

</details>

<details>
  <summary><b>cache_dir</b></summary>

The path for the cache directory where Choppr will output temporary and downloaded files.

**Type:** `Path`

**Default:** `./.cache/choppr`

**Example Usage:**
```yml
options:
  cache_dir: /tmp/choppr
```

</details>

<details>
  <summary><b>cache_timeout</b></summary>

The timeout for local cache files, like DEB packages, that aren't traced to a checksum, like RPM packages.

Expects a number followed by a unit (d = days, h = hours, m = minutes, s = seconds).

**Type:** `str | bool`

**Default:** `7d`

**Example Usage:**
```yml
options:
  cache_timeout: 24h
```

</details>

<details>
  <summary><b>clear_cache</b></summary>

Enable `clear_cache` to delete the cache directory when Choppr finishes running.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  clear_cache: true
```

</details>

<details>
  <summary><b>delete_excluded</b></summary>

Disable `delete_excluded` to keep components that are discovered to be unnecessary and marked as excluded.

**Type:** `bool`

**Default:** `true`

**Example Usage:**
```yml
options:
  delete_excluded: false
```

</details>

<details>
  <summary><b>denylist</b></summary>

A dictionary with packages to always remove from the SBOM.

The keys are purl types, and the values are a list of packages. A package has two members, name and version, both are
regex patterns.

**Type:**
```yml
denylist: # dict[PurlType, list[PackagePattern]]
  _purl_type_: # str (deb, npm, rpm, ...)
    - name: regex
      version: regex
    ...
  ...
```

**Default:** `{}`

**Example Usage:**
```yml
options:
  denylist:
    deb:
      - name: "cmake"
        version: "3.22"
    npm:
      - name: ".*"
        version: ".*"
```

</details>

<details>
  <summary><b>http_limits</b></summary>

Limits to enforce when performing HTTP requests within Choppr.

- `retries` - The number of times to retry the request if it fails
- `retry_interval` - The number of seconds to wait before retrying the request
- `timeout` - The number of seconds to wait for a request to complete before timing out

**Type:**
```yml
http_limits:  # HttpLimits
  retries: PositiveInt
  retry_interval: PositiveFloat
  timeout: PositiveFloat
```

**Default:**
```yml
http_limits:
  retries: 3
  retry_interval: 5
  timeout: 60
```

**Example Usage:**
```yml
options:
  http_limits:
    retries: 10
    retry_interval: 30
    timeout: 300
```

</details>

<details>
  <summary><b>keep_essential_os_components</b></summary>

Keep components that are essential to the operating system, to include the operating system component.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  keep_essential_os_components: true
```

</details>

<details>
  <summary><b>recursion_limit</b></summary>

A positive integer that will limit the number of recursive calls to use when checking for nested package dependencies.

**Type:** `PositiveInt`

**Default:** `10`

**Example Usage:**
```yml
options:
  recursion_limit: 20
```

</details>

<details>
  <summary><b>sort_sbom</b></summary>

Sort the output SBOM so that the elements are in the order defined in the schema.

**Type:** `bool`

**Default:** `false`

**Example Usage:**
```yml
options:
  sort_sbom: true
```

</details>

<details>
  <summary><b>strace_regex_excludes</b></summary>

An array of regex strings, used to filter the strace input. The example below shows some of the recommended regular
expressions.

**Type:** `list[str]`

**Default:** `[]`

**Example Usage:**
```yml
options:
  strace_regex_excludes:
    - "^.*project-name.*$"              # Ignore all files containing the project name to exclude source files
    - "^.*\.(c|cpp|cxx|h|hpp|o|py|s)$"  # Ignore source, header, object, and script files
    - "^/usr/share/pkgconfig$"          # Ignore pkgconfig, which is included/modified by several RPMs
    - "^/tmp$"                          # Ignore the tmp directory
    - "^bin$"                           # Ignore overly simple files, that will be matched by most RPMs
    - "^.*\.git.*$"                     # Ignore all hidden git directories and files
    - "^.*(\.\.)+.*$"                   # Ignore all relative paths containing '..'
    - "^.*(CMakeFiles.*|\.cmake)$"      # Ignore all CMake files
```

</details>

## Specificaitons for developers

- [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
- [Conventional Branch](https://conventional-branch.github.io/)
- [PEP 440 - Version Identification and Dependency Specification](https://peps.python.org/pep-0440/)