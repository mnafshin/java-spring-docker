from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.commands import cmd_benchmark_compare
from springdocker.errors import EXIT_OK, EXIT_USAGE


class CompareCommandTests(unittest.TestCase):
    def _write_csv(self, root: Path) -> Path:
        csv_path = root / "raw.csv"
        csv_path.write_text(
            "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n"
            "2026-01-01,s1,baseline,1,100,1048576,200,ok,\n"
            "2026-01-01,s1,tuned,1,80,1048576,180,ok,\n",
            encoding="utf-8",
        )
        return csv_path

    def test_compare_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = cmd_benchmark_compare(
                    project_root=root,
                    raw_csv=str(csv_path),
                    baseline_variant="baseline",
                    output_format="json",
                    scenario=None,
                )
            self.assertEqual(code, EXIT_OK)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload[0]["variant"], "baseline")
            self.assertEqual(payload[1]["variant"], "tuned")
            self.assertIn("build_delta_ms", payload[1])

    def test_compare_missing_baseline_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = cmd_benchmark_compare(
                    project_root=root,
                    raw_csv=str(csv_path),
                    baseline_variant="missing",
                    output_format="table",
                    scenario=None,
                )
            self.assertEqual(code, EXIT_USAGE)
            self.assertEqual(stdout.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
