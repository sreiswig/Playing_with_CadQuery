"""Write ``tests/drift_baseline.json`` from the current catalog builders.

Requires CadQuery. From the repository root::

    python -m tests.regen_drift_baseline

The file records, for each catalog model, the manifest and catalog
fields plus ``Volume()``, bounding-box ``xlen`` / ``ylen`` / ``zlen``,
solid count, and the exported STL triangle count. STEP and STL bytes
are not stored or compared.

If ``artifacts/manifest.json`` already records a geometry-derived field
(volume, bounding box, solid count, or triangle count) and the rebuild
disagrees beyond the drift tolerances, the mismatch is printed and the
baseline file is left unchanged.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.catalog import MODELS
from tests.drift_check import (
    BASELINE_PATH,
    REQUIRED_MODELS,
    baseline_document,
    baseline_record,
    cadquery_available,
    claim_drift,
    geometry_claims,
    manifest_by_id,
    manifest_document,
    measure_model,
)


def main(argv: list[str] | None = None) -> int:
    del argv
    if not cadquery_available():
        print("cadquery is not installed; cannot regen the drift baseline", file=sys.stderr)
        return 1

    manifest = manifest_document(ROOT)
    by_manifest = manifest_by_id(ROOT)
    catalog_ids = [str(row["id"]) for row in MODELS]
    missing = [model_id for model_id in REQUIRED_MODELS if model_id not in catalog_ids]
    unknown = [model_id for model_id in REQUIRED_MODELS if model_id not in by_manifest]
    if missing or unknown:
        print(
            "catalog/manifest is missing required models: "
            f"catalog {missing or 'ok'}, manifest {unknown or 'ok'}",
            file=sys.stderr,
        )
        return 1
    extra = [model_id for model_id in catalog_ids if model_id not in by_manifest]
    if extra:
        print(f"manifest is missing catalog models: {extra}", file=sys.stderr)
        return 1

    records = []
    drifts: list[tuple[str, list[str]]] = []
    for row in MODELS:
        model_id = str(row["id"])
        print(f"measuring {model_id}...", flush=True)
        measured = measure_model(model_id)
        entry = by_manifest[model_id]
        found = claim_drift(measured, entry)
        claims = geometry_claims(entry)
        print(
            f"{model_id}: volume_mm3={measured['volume_mm3']!r} "
            f"bbox_mm={measured['bbox_mm']!r} "
            f"solids={measured['solid_count']} "
            f"triangles={measured['stl_triangles']} "
            f"manifest_geometry_fields={len(claims)}",
            flush=True,
        )
        if found:
            drifts.append((model_id, found))
            continue
        records.append(baseline_record(model_id, measured, row, entry))

    if drifts:
        print(
            "Committed manifest geometry does not match the rebuild. "
            "Baseline file was not updated.",
            file=sys.stderr,
        )
        for model_id, lines in drifts:
            for line in lines:
                print(f"{model_id}: {line}", file=sys.stderr)
        return 1

    document = baseline_document(records, manifest)
    text = json.dumps(document, indent=2, ensure_ascii=False) + "\n"
    BASELINE_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {BASELINE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
