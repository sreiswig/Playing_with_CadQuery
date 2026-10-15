"""Copy a catalog file locally, or download it from raw GitHub."""

from __future__ import annotations

import os
import tempfile
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

# 32 MiB is well above the largest committed artifact (cat.stl, about 626 KB).
MAX_FETCH_BYTES = 32 * 1024 * 1024
DEFAULT_FETCH_TIMEOUT = 30


class FetchTooLargeError(Exception):
    """Remote artifact body exceeded the configured byte cap."""


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


def _read_bounded(resp, max_bytes: int) -> bytes:
    """Read up to ``max_bytes`` from ``resp``.

    One ``read(max_bytes + 1)`` keeps a body that is exactly at the cap and
    rejects anything larger.
    """
    data = resp.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise FetchTooLargeError(f"remote artifact exceeds {max_bytes} byte cap")
    return data


def _atomic_write_bytes(dest: Path, data: bytes) -> None:
    """Write ``data`` to a temp file next to ``dest``, then ``os.replace`` it.

    Any failure deletes the temp file and leaves ``dest`` unchanged.
    """
    fd, tmp_name = tempfile.mkstemp(
        dir=dest.parent,
        prefix=f".{dest.name}.",
        suffix=".part",
    )
    tmp_path = Path(tmp_name)
    completed = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.replace(tmp_path, dest)
        completed = True
    finally:
        if not completed:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def fetch_file(
    model_id: str,
    fmt: str,
    dest: Path,
    *,
    ref: str = "main",
    root: Path | None = None,
    urlopen=None,
    timeout: float = DEFAULT_FETCH_TIMEOUT,
    max_bytes: int = MAX_FETCH_BYTES,
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
    with opener(url, timeout=timeout) as resp:
        final = resp.geturl() if hasattr(resp, "geturl") else url
        assert_fetch_url_allowed(final)
        payload = _read_bounded(resp, max_bytes)
        _atomic_write_bytes(dest, payload)
    return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "remote", "from": url}
