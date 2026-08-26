"""Copy a catalog file locally, or download it from raw GitHub."""

from __future__ import annotations

import urllib.parse
import urllib.request
from pathlib import Path

from .catalog import MODELS, REPO_ROOT, model_url

ALLOWED_HOST = "raw.githubusercontent.com"
ALLOWED_PATH_PREFIX = "/sreiswig/Playing_with_CadQuery/"
ALLOWED_RAW_PREFIX = f"https://{ALLOWED_HOST}{ALLOWED_PATH_PREFIX}"


def assert_fetch_url_allowed(url: str) -> None:
    """Remote fetch may only hit this repo's raw.githubusercontent.com tree."""
    if not isinstance(url, str) or not url:
        raise ValueError(f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}")
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.netloc != ALLOWED_HOST:
        raise ValueError(f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}")
    if parts.username or parts.password:
        raise ValueError(f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}")
    path = urllib.parse.unquote(parts.path.replace("\\", "/"))
    segments = [s for s in path.split("/") if s not in ("", ".")]
    if ".." in segments:
        raise ValueError(f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}")
    normalized = "/" + "/".join(segments)
    if not normalized.startswith(ALLOWED_PATH_PREFIX):
        raise ValueError(f"refusing fetch: {url!r} is not under {ALLOWED_RAW_PREFIX}")


def resolve(model_id: str, fmt: str) -> tuple[dict, str]:
    match = next((m for m in MODELS if m["id"] == model_id), None)
    if match is None:
        known = ", ".join(m["id"] for m in MODELS)
        raise KeyError(f"unknown model {model_id!r}; known: {known}")
    rel = match["files"].get(fmt)
    if not rel:
        raise KeyError(f"no {fmt} for {model_id}")
    return match, rel


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
