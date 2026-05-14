from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.commands import cmd_benchmark_analyze
from springdocker.errors import EXIT_FAILURE, EXIT_OK, EXIT_USAGE


class AnalyzeCommandTests(unittest.TestCase):
    def _write_csv(self, root: Path) -> Path:
        csv_path = root / "raw.csv"
        csv_path.write_text(
            "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n"
            "2026-01-01,s1,v1,1,100,1048576,200,ok,\n"
            "2026-01-01,s1,v1,2,100,1048576,200,build_failed,\n",
            encoding="utf-8",
        )
        return csv_path

    def test_output_written_to_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            out = root / "out" / "summary.json"
            code = cmd_benchmark_analyze(
                project_root=root,
                raw_csv=str(csv_path),
                output_format="json",
                scenario=None,
                variant=None,
                output_path=str(out),
                fail_on_success_rate_below=None,
            )
            self.assertEqual(code, EXIT_OK)
            self.assertTrue(out.exists())
            self.assertIn('"scenario": "s1"', out.read_text(encoding="utf-8"))

    def test_threshold_failure_when_any_variant_below(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            stdout = StringIO()
            stderr = StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                code = cmd_benchmark_analyze(
                    project_root=root,
                    raw_csv=str(csv_path),
                    output_format="table",
                    scenario=None,
                    variant=None,
                    output_path=None,
                    fail_on_success_rate_below=75.0,
                )
            self.assertEqual(code, EXIT_FAILURE)
            self.assertIn("s1/v1", stderr.getvalue())
            self.assertIn("| Scenario | Variant |", stdout.getvalue())

    def test_threshold_validation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            stderr = StringIO()
            with redirect_stderr(stderr):
                code = cmd_benchmark_analyze(
                    project_root=root,
                    raw_csv=str(csv_path),
                    output_format="table",
                    scenario=None,
                    variant=None,
                    output_path=None,
                    fail_on_success_rate_below=150.0,
                )
            self.assertEqual(code, EXIT_USAGE)
            self.assertIn("between 0 and 100", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

