"""Pure allow/deny for remote artifact URLs. No network I/O."""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from enum import Enum

from .outcome import Err, Ok, Result

ALLOWED_HOST = "raw.githubusercontent.com"
ALLOWED_PATH_PREFIX = "/sreiswig/Playing_with_CadQuery/"
ALLOWED_RAW_PREFIX = f"https://{ALLOWED_HOST}{ALLOWED_PATH_PREFIX}"


class FetchDenyCode(Enum):
    NOT_A_URL = "not_a_url"
    NOT_HTTPS = "not_https"
    BAD_HOST = "bad_host"
    EMBEDDED_CREDENTIALS = "embedded_credentials"
    PATH_ESCAPE = "path_escape"
    OFF_PREFIX = "off_prefix"


@dataclass(frozen=True, slots=True)
class FetchDeny:
    code: FetchDenyCode
    url: object


@dataclass(frozen=True, slots=True)
class AllowedFetch:
    url: str


def fetch_deny_message(deny: FetchDeny) -> str:
    return f"refusing fetch: {deny.url!r} is not under {ALLOWED_RAW_PREFIX}"


def check_fetch_url(url: object) -> Result[AllowedFetch, FetchDeny]:
    """Allow only this repo's https raw.githubusercontent.com tree."""
    if not isinstance(url, str) or not url:
        return Err(FetchDeny(FetchDenyCode.NOT_A_URL, url))
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https":
        return Err(FetchDeny(FetchDenyCode.NOT_HTTPS, url))
    # Userinfo is part of netloc, so check it before the host equality test.
    # Otherwise user:pass@host is only reported as a bad host.
    if parts.username or parts.password:
        return Err(FetchDeny(FetchDenyCode.EMBEDDED_CREDENTIALS, url))
    if parts.netloc != ALLOWED_HOST:
        return Err(FetchDeny(FetchDenyCode.BAD_HOST, url))
    path = urllib.parse.unquote(parts.path.replace("\\", "/"))
    segments = [segment for segment in path.split("/") if segment not in ("", ".")]
    if ".." in segments:
        return Err(FetchDeny(FetchDenyCode.PATH_ESCAPE, url))
    normalized = "/" + "/".join(segments)
    if not normalized.startswith(ALLOWED_PATH_PREFIX):
        return Err(FetchDeny(FetchDenyCode.OFF_PREFIX, url))
    return Ok(AllowedFetch(url))
