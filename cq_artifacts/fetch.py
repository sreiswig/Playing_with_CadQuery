"""Copy a catalog file locally, or download it from raw GitHub."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from .catalog import MODELS, REPO_ROOT, model_url

ALLOWED_RAW_PREFIX = "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/"


def assert_fetch_url_allowed(url: object) -> None:
    if not isinstance(url, str) or not url.startswith(ALLOWED_RAW_PREFIX):
        raise ValueError(f"refused fetch URL (not on allowlist): {url!r}")


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
    opener = urlopen if urlopen is not None else urllib.request.urlopen
    with opener(url) as resp:
        assert_fetch_url_allowed(resp.geturl())
        dest.write_bytes(resp.read())
    return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "remote", "from": url}
