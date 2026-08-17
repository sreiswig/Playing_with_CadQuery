"""Copy a catalog file locally, or download it from raw GitHub."""

from __future__ import annotations

import urllib.request
from pathlib import Path

from .catalog import MODELS, REPO_ROOT, model_url


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
) -> dict:
    _match, rel = resolve(model_id, fmt)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    local = (root or REPO_ROOT) / rel
    if local.is_file():
        dest.write_bytes(local.read_bytes())
        return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "local", "from": str(local)}
    url = model_url(rel, ref=ref)
    urllib.request.urlretrieve(url, dest)
    return {"id": model_id, "fmt": fmt, "path": str(dest), "source": "remote", "from": url}
