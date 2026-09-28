"""Copy a catalog file locally, or download it from raw GitHub."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from .catalog import MODELS, REPO_ROOT, model_url
from .catalog_lookup import lookup_artifact, lookup_deny_message
from .fetch_policy import (
    ALLOWED_HOST,
    ALLOWED_PATH_PREFIX,
    ALLOWED_RAW_PREFIX,
    check_fetch_url,
    fetch_deny_message,
)
from .outcome import Err


def assert_fetch_url_allowed(url: str) -> None:
    """Remote fetch may only hit this repo's raw.githubusercontent.com tree."""
    checked = check_fetch_url(url)
    if isinstance(checked, Err):
        raise ValueError(fetch_deny_message(checked.error))


def resolve(model_id: str, fmt: str) -> tuple[dict, str]:
    found = lookup_artifact(MODELS, model_id, fmt)
    if isinstance(found, Err):
        raise KeyError(lookup_deny_message(found.error, include_known=True))
    match = next(row for row in MODELS if row["id"] == model_id)
    return match, found.value.relpath


def fetch_file(
    model_id: str,
    fmt: str,
    dest: Path,
    *,
    ref: str = "main",
    root: Path | None = None,
    urlopen=None,
) -> dict:
    _match, rel = resolve(model_id, fmt)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    local = (root or REPO_ROOT) / rel
    if local.is_file():
        dest.write_bytes(local.read_bytes())
        return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "local", "from": str(local)}
    url = model_url(rel, ref=ref)
    assert_fetch_url_allowed(url)
    opener = urlopen or urllib.request.urlopen
    with opener(url) as resp:
        final = resp.geturl() if hasattr(resp, "geturl") else url
        assert_fetch_url_allowed(final)
        dest.write_bytes(resp.read())
    return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "remote", "from": url}
