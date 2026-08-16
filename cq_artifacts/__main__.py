"""CLI: python -m cq_artifacts list|export|url|path"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .catalog import MODELS, REPO_ROOT, build_manifest, model_url, write_manifest


def _cmd_list(_args: argparse.Namespace) -> int:
    print(json.dumps(build_manifest(), indent=2))
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    from .export import export_all, export_model

    root = Path(args.root) if args.root else REPO_ROOT
    if args.id:
        written = {args.id: export_model(args.id, root=root)}
        write_manifest(root)
    else:
        written = export_all(root=root)
    print(json.dumps(written, indent=2))
    return 0


def _cmd_url(args: argparse.Namespace) -> int:
    match = next((m for m in MODELS if m["id"] == args.id), None)
    if match is None:
        print(f"unknown model {args.id!r}", file=sys.stderr)
        return 1
    rel = match["files"].get(args.fmt)
    if not rel:
        print(f"no {args.fmt} for {args.id}", file=sys.stderr)
        return 1
    print(model_url(rel, ref=args.ref))
    return 0


def _cmd_path(args: argparse.Namespace) -> int:
    match = next((m for m in MODELS if m["id"] == args.id), None)
    if match is None:
        print(f"unknown model {args.id!r}", file=sys.stderr)
        return 1
    rel = match["files"].get(args.fmt)
    if not rel:
        print(f"no {args.fmt} for {args.id}", file=sys.stderr)
        return 1
    print(REPO_ROOT / rel)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m cq_artifacts",
        description="List and export CadQuery models for other programs.",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="Print artifacts/manifest.json (no CadQuery needed)")
    p_list.set_defaults(func=_cmd_list)

    p_export = sub.add_parser("export", help="Rebuild STEP/STL (needs CadQuery)")
    p_export.add_argument("--id", help="Single model id (default: all)")
    p_export.add_argument("--root", help="Repo root override")
    p_export.set_defaults(func=_cmd_export)

    p_url = sub.add_parser("url", help="Print raw GitHub URL for a file")
    p_url.add_argument("id")
    p_url.add_argument("fmt", choices=["step", "stl"])
    p_url.add_argument("--ref", default="main")
    p_url.set_defaults(func=_cmd_url)

    p_path = sub.add_parser("path", help="Print local path for a file")
    p_path.add_argument("id")
    p_path.add_argument("fmt", choices=["step", "stl"])
    p_path.set_defaults(func=_cmd_path)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
