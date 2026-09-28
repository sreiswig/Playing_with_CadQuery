"""Build STEP/STL for catalog models. Requires CadQuery only at export time."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from .catalog import MODELS, REPO_ROOT, write_manifest
from .catalog_lookup import lookup_deny_message, lookup_model
from .outcome import Err


def _load_builder(spec: str):
    mod_name, fn_name = spec.split(":", 1)
    module = importlib.import_module(mod_name)
    return getattr(module, fn_name)


def _export_shape(shape: Any, dest: Path) -> None:
    import cadquery as cq

    dest.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shape, str(dest))


def export_model(model_id: str, root: Path | None = None) -> dict[str, str]:
    root = root or REPO_ROOT
    found = lookup_model(MODELS, model_id)
    if isinstance(found, Err):
        raise KeyError(lookup_deny_message(found.error, include_known=True))
    row = found.value

    shape = _load_builder(row.builder)()
    written: dict[str, str] = {}
    for fmt, rel in row.files:
        dest = root / rel
        _export_shape(shape, dest)
        written[fmt] = rel
    return written


def export_all(root: Path | None = None) -> dict[str, dict[str, str]]:
    root = root or REPO_ROOT
    out = {m["id"]: export_model(m["id"], root=root) for m in MODELS}
    write_manifest(root)
    return out
