# Artifacts

`manifest.json` is the machine-readable index (ids, formats, paths, raw GitHub URLs).

STEP files currently live at the repo root (`cat.step`, `drone.step`, `sonic.step`,
`box.step`, `through-hole.step`, `m3-shcs.step`, `m3-nut.step`,
`headset-earcup.step`, `headset-headband.step`, `headset-yoke.step`,
`headset.step`, `bottle-rack-guide.step`, `bottle-rack-gate.step`,
`bottle-rack.step`) so existing links keep working.
The bottle-rack cut list is `artifacts/bottle-rack/cut-list.json`
(and `cut-list.csv`), generated from the same parameters as the solid.
STL lands under `artifacts/<id>/` when
you run `python -m cq_artifacts export`.
