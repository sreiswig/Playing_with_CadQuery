# Agent guide — Playing_with_CadQuery

CadQuery playground. Two solid models live here: **cat** and **drone**.
Other scripts (`tutorial.py`, `visuals.py`, `workplane_examples.py`) are
learning notes, not export targets.

## Environment

```bash
# Nix + devenv (preferred)
direnv allow   # or: devenv shell
# or: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
```

`requirements.txt` is just `cadquery`. OpenCascade libs come from `devenv.nix`.

## List artifacts (no CadQuery)

```bash
python -m cq_artifacts list
```

That prints the same document as [`artifacts/manifest.json`](artifacts/manifest.json).

## Fetch a file for another program

**Remote (any agent, no checkout):**

- Manifest: https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/artifacts/manifest.json
- Cat STEP: https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/cat.step
- Drone STEP: https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/main/drone.step

Or:

```bash
python -m cq_artifacts url cat step
python -m cq_artifacts url drone stl
```

STL URLs 404 until someone has run `export` and committed the mesh (or you
generate it locally). STEP at repo root is already committed.

**Local:**

```bash
python -m cq_artifacts path cat step
# /.../Playing_with_CadQuery/cat.step
```

Use STEP in FreeCAD / other CAD. Use STL in slicers, Blender, three.js
(convert), game engines.

Units are millimetres.

## Rebuild

```bash
python -m cq_artifacts export          # all models → STEP + STL
python -m cq_artifacts export --id cat
```

Export imports `create_cat` / `create_drone` and writes:

| id    | STEP (committed) | STL (generated)            |
|-------|------------------|----------------------------|
| cat   | `cat.step`       | `artifacts/cat/cat.stl`    |
| drone | `drone.step`     | `artifacts/drone/drone.stl`|

Then refreshes `artifacts/manifest.json`.

Do not add a server or auth. This repo is files + a CLI.

## Adding a model

1. Put a `create_<id>()` in a module that returns a CadQuery solid.
2. Register it in `cq_artifacts/catalog.py` `MODELS`.
3. Run `python -m cq_artifacts export --id <id>`.
4. Commit STEP if it is small. Skip huge binaries.

## Out of scope

- glTF/GLB (CadQuery/OCP here has no cheap exporter)
- Tutorial/visual scripts
- Paid GitHub Actions
