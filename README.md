# Playing_with_CadQuery

Small CadQuery playground (Nix devenv). Models: a cat, a quadcopter, a
stylized Sonic-like hedgehog (original geometry), a parametric **box**,
an M3 **through-hole** plate, an **m3-shcs** socket-head envelope, an
**m3-nut** hex-nut envelope, a parametric **headset** shell kit
(earcup, headband, hinge yoke, assembly), and a parametric **bottle rack**
(lane guide, outlet gate, module).

Mechanical roadmap (ranked list v0.1): [`docs/MECH_CATALOG.md`](docs/MECH_CATALOG.md).

**Agents:** read [AGENTS.md](AGENTS.md). List and fetch files with
`python -m cq_artifacts list` or the raw URLs in
[artifacts/manifest.json](artifacts/manifest.json).

```bash
direnv allow                 # or devenv shell
python -m cq_artifacts list
python -m cq_artifacts export
```

Humans: `cat_model.py`, `drone.py`, `sonic.py`, `box.py`, `through_hole.py`,
`m3_shcs.py`, `m3_nut.py`, `headset.py`, and `bottle_rack.py` are the builders.
Open the `.step` files in FreeCAD or CQ-Editor.
