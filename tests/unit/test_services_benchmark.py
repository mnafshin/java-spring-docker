from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.services.benchmark_service import (
    analyze_csv,
    render_comparison,
    validate_reproducibility_with_legacy,
)


class BenchmarkServiceTests(unittest.TestCase):
    def _write_csv(self, root: Path) -> Path:
        csv_path = root / "raw.csv"
        csv_path.write_text(
            "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n"
            "2026-01-01,s1,baseline,1,100,1048576,200,ok,\n"
            "2026-01-01,s1,tuned,1,80,1048576,180,ok,\n",
            encoding="utf-8",
        )
        return csv_path

    def test_validate_reproducibility_with_legacy_rejects_controls(self) -> None:
        with self.assertRaises(ValueError):
            validate_reproducibility_with_legacy(
                use_legacy_scripts=True,
                cpuset_cpus="0-1",
                memory_limit=None,
                warmup_runs=0,
                normalized_runtime=False,
            )

    def test_render_comparison_outputs_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            rendered = render_comparison(root, str(csv_path), "baseline", "table", None)
            self.assertIn("| Scenario | Variant |", rendered)
            self.assertIn("tuned", rendered)

    def test_analyze_csv_flags_missing_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            csv_path = self._write_csv(root)
            outcome = analyze_csv(
                project_root=root,
                raw_csv=str(csv_path),
                output_format="json",
                scenario=None,
                variant=None,
                output_path=None,
                fail_on_success_rate_below=None,
                baseline_path="missing.json",
                fail_on_regression_above=20.0,
            )
            self.assertIsNotNone(outcome.baseline_missing)
            self.assertEqual(outcome.regression_violations, ())


if __name__ == "__main__":
    unittest.main()

