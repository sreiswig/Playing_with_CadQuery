# Playing_with_CadQuery

Small CadQuery playground (Nix devenv). Models: a cat and a quadcopter.

**Agents:** read [AGENTS.md](AGENTS.md). List and fetch files with
`python -m cq_artifacts list` or the raw URLs in
[artifacts/manifest.json](artifacts/manifest.json).

```bash
direnv allow                 # or devenv shell
python -m cq_artifacts list
python -m cq_artifacts export
```

Humans: `cat_model.py` and `drone.py` are the builders. Open the `.step`
files in FreeCAD or CQ-Editor.
