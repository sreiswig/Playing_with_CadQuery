"""Machine-readable catalog. Importing this module does not require CadQuery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = "artifacts/manifest.json"
RAW_BASE = "https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/"

# Builders are imported only when exporting. Paths may be repo-root STEP
# files that already exist, or artifacts/<id>/ files written by export.
MODELS: list[dict[str, Any]] = [
    {
        "id": "cat",
        "source": "cat_model.py",
        "builder": "cat_model:create_cat",
        "units": "mm",
        "description": "Vibe-coded cat (body, head, ears, legs, tail).",
        "files": {
            "step": "cat.step",
            "stl": "artifacts/cat/cat.stl",
        },
    },
    {
        "id": "drone",
        "source": "drone.py",
        "builder": "drone:create_drone",
        "units": "mm",
        "description": "Quadcopter: body, four arms, motors, simple props.",
        "files": {
            "step": "drone.step",
            "stl": "artifacts/drone/drone.stl",
        },
    },
    {
        "id": "sonic",
        "source": "sonic.py",
        "builder": "sonic:create_sonic",
        "units": "mm",
        "description": "Stylized chibi hedgehog (quills, muzzle, gloves, oversized shoes). Original geometry.",
        "files": {
            "step": "sonic.step",
            "stl": "artifacts/sonic/sonic.stl",
        },
    },
    {
        "id": "box",
        "source": "box.py",
        "builder": "box:create_box",
        "units": "mm",
        "description": "Parametric rectangular prism (CadQuery box). Defaults 10×10×10 mm.",
        "files": {
            "step": "box.step",
            "stl": "artifacts/box/box.stl",
        },
    },
    {
        "id": "through-hole",
        "source": "through_hole.py",
        "builder": "through_hole:create_through_hole",
        "units": "mm",
        "description": (
            "Plate with an ISO 273 medium-series M3 clearance hole (3.4 mm). "
            "Demo plate 20×20×3 mm (not from a standard), hole centred."
        ),
        "files": {
            "step": "through-hole.step",
            "stl": "artifacts/through-hole/through-hole.stl",
        },
    },
    {
        "id": "m3-shcs",
        "source": "m3_shcs.py",
        "builder": "m3_shcs:create_m3_shcs",
        "units": "mm",
        "description": (
            "ISO 4762 M3 socket head cap screw envelope (no thread helix). "
            "Default length 10 mm. ISO 888 preferred lengths 5–30 mm."
        ),
        "files": {
            "step": "m3-shcs.step",
            "stl": "artifacts/m3-shcs/m3-shcs.stl",
        },
    },
    {
        "id": "m3-nut",
        "source": "m3_nut.py",
        "builder": "m3_nut:create_m3_nut",
        "units": "mm",
        "description": (
            "ISO 4032 style 1 M3 hex nut envelope (no thread helix). "
            "Across flats 5.5 mm, height 2.4 mm, bore 3.0 mm."
        ),
        "files": {
            "step": "m3-nut.step",
            "stl": "artifacts/m3-nut/m3-nut.stl",
        },
    },
    {
        "id": "headset-earcup",
        "source": "headset.py",
        "builder": "headset:create_headset_earcup",
        "units": "mm",
        "description": (
            "Circumaural earcup shell and back cover. Default seat fits a "
            "50 mm dynamic driver (40–50 mm), with a pad lip, PCB and LiPo bay, "
            "mic-boom port, and flex pass-through. Cover holes are 3.4 mm."
        ),
        "files": {
            "step": "headset-earcup.step",
            "stl": "artifacts/headset-earcup/headset-earcup.stl",
        },
    },
    {
        "id": "headset-headband",
        "source": "headset.py",
        "builder": "headset:create_headset_headband",
        "units": "mm",
        "description": (
            "Parametric headband. Default inner radius 105 mm over a 110° arc, "
            "with an M3 clearance extension slot (3.4 mm) in each leg."
        ),
        "files": {
            "step": "headset-headband.step",
            "stl": "artifacts/headset-headband/headset-headband.stl",
        },
    },
    {
        "id": "headset-yoke",
        "source": "headset.py",
        "builder": "headset:create_headset_yoke",
        "units": "mm",
        "description": (
            "Hinge yoke. Slider plate and clevis join the headband slot to the "
            "earcup trunnion. Swivels on the M3 clamp screw; hinges on an M3 pin."
        ),
        "files": {
            "step": "headset-yoke.step",
            "stl": "artifacts/headset-yoke/headset-yoke.stl",
        },
    },
    {
        "id": "headset",
        "source": "headset.py",
        "builder": "headset:create_headset",
        "units": "mm",
        "description": (
            "Wireless gaming headset shell kit: headband, two earcups, yokes, "
            "covers, and ISO 4762 M3 socket-head screws in 3.4 mm clearance holes."
        ),
        "files": {
            "step": "headset.step",
            "stl": "artifacts/headset/headset.stl",
        },
    },
    {
        "id": "bottle-rack-guide",
        "source": "bottle_rack.py",
        "builder": "bottle_rack:create_bottle_rack_guide",
        "units": "mm",
        "description": (
            "Printed lane guide for the bottle rack. Default length matches a "
            "5-deep lane of 110 mm bottles. Three 3.4 mm flange holes."
        ),
        "files": {
            "step": "bottle-rack-guide.step",
            "stl": "artifacts/bottle-rack-guide/bottle-rack-guide.stl",
        },
    },
    {
        "id": "bottle-rack-gate",
        "source": "bottle_rack.py",
        "builder": "bottle_rack:create_bottle_rack_gate",
        "units": "mm",
        "description": (
            "Printed outlet lift gate with a finger notch. Default opening "
            "suits a 110 mm bottle. One gate per lane."
        ),
        "files": {
            "step": "bottle-rack-gate.step",
            "stl": "artifacts/bottle-rack-gate/bottle-rack-gate.stl",
        },
    },
    {
        "id": "bottle-rack",
        "source": "bottle_rack.py",
        "builder": "bottle_rack:create_bottle_rack",
        "units": "mm",
        "description": (
            "Gravity-fed FIFO bottle rack. Default module is 3 lanes by 5 deep "
            "for a 110×310 mm bottle at 7°, plywood plus 20×20 mm 2020 envelopes, "
            "with lane guides, lift gates, sensor holes, a cable groove, side-tile "
            "pins, and a 2-high stack interlock. Cut list: artifacts/bottle-rack/cut-list.json."
        ),
        "files": {
            "step": "bottle-rack.step",
            "stl": "artifacts/bottle-rack/bottle-rack.stl",
        },
    },
]


def models() -> list[dict[str, Any]]:
    return [dict(m) for m in MODELS]


def model_url(relpath: str, *, ref: str = "main") -> str:
    base = RAW_BASE.replace("/main/", f"/{ref}/")
    return base + relpath.lstrip("/")


def load_manifest(root: Path | None = None) -> dict[str, Any]:
    path = (root or REPO_ROOT) / MANIFEST_NAME
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest(*, ref: str = "main") -> dict[str, Any]:
    entries = []
    for m in MODELS:
        files = {}
        for fmt, rel in m["files"].items():
            files[fmt] = {
                "path": rel,
                "url": model_url(rel, ref=ref),
            }
        entries.append(
            {
                "id": m["id"],
                "source": m["source"],
                "builder": m["builder"],
                "units": m["units"],
                "description": m["description"],
                "files": files,
            }
        )
    return {
        "version": 1,
        "units": "mm",
        "raw_base": model_url("", ref=ref),
        "models": entries,
    }


def write_manifest(root: Path | None = None, *, ref: str = "main") -> Path:
    root = root or REPO_ROOT
    path = root / MANIFEST_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(build_manifest(ref=ref), indent=2) + "\n", encoding="utf-8")
    return path
