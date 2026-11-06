"""Export path refreshes the bottle-rack cut list. No CadQuery."""

from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cq_artifacts.bottle_rack_dims import cut_list_csv, cut_list_json, write_cut_list  # noqa: E402
from cq_artifacts.export import export_all, export_model  # noqa: E402

_BOTTLE_RACK_IDS = ("bottle-rack", "bottle-rack-guide", "bottle-rack-gate")


@contextmanager
def _stub_geometry():
    """Skip CadQuery. ``export_model`` still walks the real catalog paths."""

    def load_builder(spec: str):
        def build():
            return spec

        return build

    def export_shape(shape, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("stub\n", encoding="utf-8")

    with (
        patch("cq_artifacts.export._load_builder", load_builder),
        patch("cq_artifacts.export._export_shape", export_shape),
    ):
        yield


def _assert_default_cut_list(test: unittest.TestCase, root: Path) -> None:
    cut_dir = root / "artifacts" / "bottle-rack"
    test.assertEqual(
        (cut_dir / "cut-list.json").read_text(encoding="utf-8"),
        cut_list_json(),
    )
    test.assertEqual(
        (cut_dir / "cut-list.csv").read_text(encoding="utf-8"),
        cut_list_csv(),
    )


class ExportCutListTests(unittest.TestCase):
    def test_each_bottle_rack_export_refreshes_the_default_cut_list(self):
        for model_id in _BOTTLE_RACK_IDS:
            with self.subTest(model=model_id):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    cut_dir = root / "artifacts" / "bottle-rack"
                    cut_dir.mkdir(parents=True)
                    (cut_dir / "cut-list.json").write_text("stale\n", encoding="utf-8")
                    (cut_dir / "cut-list.csv").write_text("stale\n", encoding="utf-8")
                    with (
                        _stub_geometry(),
                        patch(
                            "cq_artifacts.bottle_rack_dims.write_cut_list",
                            wraps=write_cut_list,
                        ) as wrote,
                    ):
                        exported = export_model(model_id, root=root)
                    self.assertEqual(wrote.call_count, 1)
                    self.assertEqual(wrote.call_args.args, (cut_dir,))
                    self.assertEqual(wrote.call_args.kwargs, {})
                    self.assertIn("step", exported.files)
                    self.assertIn("stl", exported.files)
                    self.assertTrue((root / exported.files["step"]).is_file())
                    self.assertTrue((root / exported.files["stl"]).is_file())
                    _assert_default_cut_list(self, root)

    def test_export_all_refreshes_a_stale_cut_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cut_dir = root / "artifacts" / "bottle-rack"
            cut_dir.mkdir(parents=True)
            (cut_dir / "cut-list.json").write_text("{}\n", encoding="utf-8")
            (cut_dir / "cut-list.csv").write_text("old\n", encoding="utf-8")
            with (
                _stub_geometry(),
                patch(
                    "cq_artifacts.bottle_rack_dims.write_cut_list",
                    wraps=write_cut_list,
                ) as wrote,
            ):
                written = export_all(root=root)
            self.assertGreaterEqual(wrote.call_count, 1)
            for call in wrote.call_args_list:
                self.assertEqual(call.args, (cut_dir,))
                self.assertEqual(call.kwargs, {})
            for model_id in _BOTTLE_RACK_IDS:
                self.assertIn(model_id, written)
            _assert_default_cut_list(self, root)
            self.assertTrue((root / "artifacts" / "manifest.json").is_file())

    def test_other_models_leave_an_existing_cut_list_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cut_dir = root / "artifacts" / "bottle-rack"
            cut_dir.mkdir(parents=True)
            (cut_dir / "cut-list.json").write_text("keep\n", encoding="utf-8")
            (cut_dir / "cut-list.csv").write_text("keep\n", encoding="utf-8")
            with _stub_geometry():
                export_model("box", root=root)
            self.assertEqual(
                (cut_dir / "cut-list.json").read_text(encoding="utf-8"),
                "keep\n",
            )
            self.assertEqual(
                (cut_dir / "cut-list.csv").read_text(encoding="utf-8"),
                "keep\n",
            )

    def test_cli_export_id_writes_the_cut_list_from_an_empty_root(self):
        from cq_artifacts.__main__ import main

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stdout = io.StringIO()
            with _stub_geometry(), redirect_stdout(stdout):
                code = main(["export", "--id", "bottle-rack-gate", "--root", str(root)])
            self.assertEqual(code, 0)
            self.assertIn("bottle-rack-gate.step", stdout.getvalue())
            _assert_default_cut_list(self, root)
            self.assertTrue((root / "artifacts" / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
