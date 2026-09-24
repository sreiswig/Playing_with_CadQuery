"""Pure catalog id/format lookup. No filesystem and no CadQuery."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .outcome import Err, Ok, Result


class LookupCode(Enum):
    UNKNOWN_MODEL = "unknown_model"
    MISSING_FORMAT = "missing_format"


@dataclass(frozen=True, slots=True)
class LookupDeny:
    code: LookupCode
    model_id: str
    fmt: str | None
    known_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ModelRow:
    id: str
    source: str
    builder: str
    units: str
    description: str
    files: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    model_id: str
    fmt: str
    relpath: str


def lookup_deny_message(deny: LookupDeny, *, include_known: bool) -> str:
    if deny.code is LookupCode.UNKNOWN_MODEL:
        if include_known:
            known = ", ".join(deny.known_ids)
            return f"unknown model {deny.model_id!r}; known: {known}"
        return f"unknown model {deny.model_id!r}"
    if deny.fmt is None:
        return f"no format for {deny.model_id}"
    return f"no {deny.fmt} for {deny.model_id}"


def lookup_model(
    models: Sequence[Mapping[str, Any]],
    model_id: str,
) -> Result[ModelRow, LookupDeny]:
    known = tuple(str(row["id"]) for row in models if "id" in row)
    for row in models:
        if row.get("id") != model_id:
            continue
        files_raw = row.get("files") or {}
        files = tuple(
            (str(fmt), str(rel))
            for fmt, rel in files_raw.items()
            if rel
        )
        return Ok(
            ModelRow(
                id=str(row["id"]),
                source=str(row.get("source", "")),
                builder=str(row.get("builder", "")),
                units=str(row.get("units", "")),
                description=str(row.get("description", "")),
                files=files,
            )
        )
    return Err(
        LookupDeny(
            code=LookupCode.UNKNOWN_MODEL,
            model_id=model_id,
            fmt=None,
            known_ids=known,
        )
    )


def lookup_artifact(
    models: Sequence[Mapping[str, Any]],
    model_id: str,
    fmt: str,
) -> Result[ArtifactRef, LookupDeny]:
    found = lookup_model(models, model_id)
    if isinstance(found, Err):
        deny = found.error
        return Err(
            LookupDeny(
                code=deny.code,
                model_id=model_id,
                fmt=fmt,
                known_ids=deny.known_ids,
            )
        )
    for name, relpath in found.value.files:
        if name == fmt:
            return Ok(ArtifactRef(model_id=found.value.id, fmt=fmt, relpath=relpath))
    return Err(
        LookupDeny(
            code=LookupCode.MISSING_FORMAT,
            model_id=model_id,
            fmt=fmt,
            known_ids=tuple(str(row["id"]) for row in models if "id" in row),
        )
    )
