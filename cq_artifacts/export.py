"""Build STEP/STL for catalog models. Requires CadQuery only at export time."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class ExportedModel:
    """Files written for one catalog model, plus the shape that was exported.

    ``files`` maps each format (``step``, ``stl``) to a path relative to the
    export root. ``shape`` is the catalog builder's return value.
    """

    files: dict[str, str]
    shape: Any


def export_model(model_id: str, root: Path | None = None) -> ExportedModel:
    """Build one catalog model and write its STEP and STL under ``root``."""
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
    return ExportedModel(files=written, shape=shape)


def export_all(root: Path | None = None) -> dict[str, dict[str, str]]:
    root = root or REPO_ROOT
    out = {m["id"]: export_model(m["id"], root=root).files for m in MODELS}
    write_manifest(root)
    return out
