"""Utility functions used to handle HTTP requests."""

from __future__ import annotations

import bz2
import contextlib
import gzip
import lzma
import time

from http.client import RemoteDisconnected
from typing import TYPE_CHECKING

import requests

from pydantic import HttpUrl, SecretStr
from requests.auth import HTTPBasicAuth
from requests.exceptions import ProxyError

from choppr.types.shares import Shares


if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from requests import Response

    from choppr.types.configuration import Credentials


__all__ = ["download", "download_compressed", "download_raw", "get", "get_auth_and_verify"]
__author__ = "Jesse Boswell <jesse.a.boswell@lmco.com>"
__copyright__ = "Copyright (C) 2025 Lockheed Martin Corporation"
__license__ = "MIT License"


def get(url: HttpUrl, auth: HTTPBasicAuth | None = None, verify: str | bool = True) -> Response:
    """Perform an HTTP get request with the provided parameters.

    Arguments:
        url: The URL to access
        auth: The credentials needed to access the URL (default None)
        verify: The certificate needed to access the URL (default True)

    Returns:
        Response: The response from the request
    """
    limits = Shares.options.http_limits

    if url.scheme != "https" and auth:
        Shares.log.warning(f"Weak authentication is being used with an insecure URL: {url}")

    for attempt in range(limits.retries):
        if attempt > 0:
            time.sleep(limits.retry_interval)

        with contextlib.suppress(RemoteDisconnected):
            response = requests.get(
                str(url),
                auth=auth,
                stream=True,
                verify=verify,
                timeout=limits.timeout,
            )
            if response.ok:
                return response
    return response


def download_raw(url: HttpUrl, auth: HTTPBasicAuth | None = None, verify: str | bool = True) -> bytes | None:
    """Download the raw content with the provided parameters.

    Arguments:
        url: The URL to access
        auth: The credentials needed to access the URL (default None)
        verify: The certificate needed to access the URL (default True)

    Returns:
        bytes | None: The raw content if the request is successful
    """
    response = get(url, auth, verify)

    return response.content if response.ok else None


def download(
    url: HttpUrl,
    auth: HTTPBasicAuth | None = None,
    verify: str | bool = True,
    encoding: str = "utf-8",
) -> str | None:
    """Download the content and decode with the provided parameters.

    Arguments:
        url: The URL to access
        auth: The credentials needed to access the URL (default None)
        verify: The certificate needed to access the URL (default True)
        encoding: The encoding to use when decoding the content (default "utf-8")

    Returns:
        str | None: The decoded content if the request is successful
    """
    with contextlib.suppress(ProxyError):
        if raw := download_raw(url, auth, verify):
            return raw.decode(encoding)

    return None


def download_compressed(
    url: HttpUrl,
    auth: HTTPBasicAuth | None = None,
    verify: str | bool = True,
    encoding: str = "utf-8",
) -> str | None:
    """Download the content, then decoompress and decode it with the provided parameters.

    Arguments:
        url: The URL to access
        auth: The credentials needed to access the URL (default None)
        verify: The certificate needed to access the URL (default True)
        encoding: The encoding to use when decoding the content (default "utf-8")

    Returns:
        str | None: The decompressed and decoded content if the request is successful
    """
    decompress: dict[str, Callable[[bytes], bytes]] = {
        "": lambda c: c,
        ".xz": lzma.decompress,
        ".gz": gzip.decompress,
        ".tgz": gzip.decompress,
        ".bzip2": bz2.decompress,
    }

    for suffix, method in decompress.items():
        with contextlib.suppress(ProxyError):
            if (raw := download_raw(HttpUrl(f"{url}{suffix}"), auth, verify)) and (
                output := method(raw).decode(encoding)
            ):
                return output

    return None


def get_auth_and_verify(
    credentials: Credentials | None = None, certificate: Path | None = None
) -> tuple[HTTPBasicAuth | None, str | bool]:
    """Get the authentication credentials and certificate.

    Arguments:
        credentials: The credentials object from a repository (default None)
        certificate: The path to a certificate (default None)

    Returns:
        tuple[HTTPBasicAuth | None, str | bool]: Credentials and certificate
    """
    auth = None
    if credentials and isinstance(credentials.password, SecretStr):
        auth = HTTPBasicAuth(username=credentials.username, password=credentials.password.get_secret_value())

    return (auth, str(certificate) if certificate else True)
