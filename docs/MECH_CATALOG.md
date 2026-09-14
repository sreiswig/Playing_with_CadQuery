# Mechanical catalog v0.1

Ranked roadmap of parametric FDM+CadQuery parts for this repo. **box** lands in this PR; later rows are planned builds, not yet implemented.

## Rules

- **Stack:** FDM + CadQuery only.
- **Default fastener thread:** M3 per ISO 262 (M3×0.5). Exception: **t-nut-m5** stays M5 (Misumi HNTA5-5 / 2020 T-slot).
- **Hardware owns ranks 1–16** (complexity 1–3). **Mechanisms own ranks 17–25** (complexity 4–5).
- **Envelope only:** model outer geometry and clearances; do not invent ISO dimensions beyond cited envelopes.
- **Cite specs** in notes (ISO / DIN / McMaster / Misumi / Gates as applicable).
- **Packaging** matches existing models (**cat** / **drone** / **sonic**): register in `cq_artifacts/catalog.py` `MODELS`, commit STEP at repo root and STL under `artifacts/<id>/`, refresh `artifacts/manifest.json`.
- **Fetch allowlist:** `https://raw.githubusercontent.com/sreiswig/Playing_with_CadQuery/` only (see `cq_artifacts/fetch.py`).
- **Build next after box:** **through-hole** → **m3-shcs**.

## Ranked list (v0.1)

| # | id | name | cx | params | notes / cites |
|---|----|------|----|--------|---------------|
| 1 | box | box | 1 | L,W,H | CadQuery primitive (landed this PR) |
| 2 | cylinder | cylinder | 1 | d,h | shaft/boss stock |
| 3 | through-hole | through hole | 1 | d,t | ISO 273 medium (M3=3.4 mm) |
| 4 | m3-shcs | M3 SHCS | 1 | length ISO 888 | ISO 4762 envelope dk max 5.5 / k max 3.0 / s 2.5; M3×0.5 ISO 262; not ISO 4017 |
| 5 | m3-nut | M3 hex nut | 1 | style 1 | ISO 4032 |
| 6 | m3-washer | M3 washer | 1 | series | ISO 7089 normal |
| 7 | counterbore | SHCS counterbore | 2 | thread,t | ISO 4762 head envelope + ISO 273 hole; DIN 974-1 only for shop CB |
| 8 | plate | plate | 2 | L,W,t,hole grid | printable |
| 9 | boss | boss | 2 | d,h,hole | pad on plate |
| 10 | heatset-boss | heat-set boss | 2 | insert series | McMaster 94180 / ruthex M3-short |
| 11 | standoff-m3 | M3 hex standoff | 3 | length,sex | McMaster hex standoff (NOT DIN 6334) |
| 12 | dowel-pin | dowel pin | 3 | d,L,fit | ISO 2338 |
| 13 | bushing | flange bushing | 3 | ID,OD,L | ISO 4379 |
| 14 | bearing-608 | 608 bearing | 3 | designated | ISO 15 8×22×7 |
| 15 | extrusion-2020 | 2020 T-slot | 3 | L | Misumi HFS5-2020 / 80-20 2020 |
| 16 | t-nut-m5 | M5 drop-in T-nut | 3 | — | Misumi HNTA5-5; stays M5 |
| 17 | hinge-pin | pin hinge | 4 | leaf,pin d | printed leaves + ISO 2338; optional ISO 4379 |
| 18 | latch | latch | 4 | throw,screw | m3-shcs + heatset-boss |
| 19 | pulley-gt2 | GT2 pulley | 4 | teeth,bore | Gates PowerGrip GT2 2 mm; bore 5 mm NEMA-17 or 8 mm 608; M3 set-screw not shaft |
| 20 | spur-gear | spur gear | 4 | z,module,bore | ISO 53 20°, ISO 54 m=1 start |
| 21 | leadscrew-nut-t8 | T8 lead nut | 4 | lead | ISO 2901/2902; default Tr8×8 P2 4-start; Tr8×2 optional |
| 22 | linear-slide | linear slide | 4 | travel | printed dovetail first |
| 23 | four-bar | four-bar | 5 | link lengths | links + ISO 2338 + M3 |
| 24 | enclosure-m3 | M3 enclosure | 5 | L,W,H | box + heat-set + m3-shcs + plate lid |
| 25 | gearbox-2stage | 2-stage gearbox | 5 | ratio,module | two spur-gear + bearing-608 + enclosure |

## Complexity bands

| cx | meaning | ranks |
|----|---------|-------|
| 1–3 | Hardware / stock primitives | 1–16 |
| 4–5 | Mechanisms / assemblies | 17–25 |

## Status

| id | status |
|----|--------|
| box | Implemented (`box.py` / `create_box`) |
| all others | Planned — do not invent ISO dimensions when implementing |

See [AGENTS.md](../AGENTS.md) for export/fetch conventions.
