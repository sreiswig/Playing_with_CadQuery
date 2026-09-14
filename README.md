# Playing_with_CadQuery

Small CadQuery playground (Nix devenv). Models: a cat, a quadcopter, a
stylized Sonic-like hedgehog (original geometry), and a parametric **box**
(first mechanical catalog part).

Mechanical roadmap (ranked list v0.1): [`docs/MECH_CATALOG.md`](docs/MECH_CATALOG.md).

**Agents:** read [AGENTS.md](AGENTS.md). List and fetch files with
`python -m cq_artifacts list` or the raw URLs in
[artifacts/manifest.json](artifacts/manifest.json).

```bash
direnv allow                 # or devenv shell
python -m cq_artifacts list
python -m cq_artifacts export
```

Humans: `cat_model.py`, `drone.py`, `sonic.py`, and `box.py` are the builders.
Open the `.step` files in FreeCAD or CQ-Editor.
