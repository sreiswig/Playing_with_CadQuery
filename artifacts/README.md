# Artifacts

`manifest.json` is the machine-readable index (ids, formats, paths, raw GitHub URLs).

STEP files currently live at the repo root (`cat.step`, `drone.step`) so existing
links keep working. STL lands under `artifacts/<id>/` when you run
`python -m cq_artifacts export`.
