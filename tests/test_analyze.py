from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.analyze import format_json, format_table, summarize_csv


class AnalyzeTests(unittest.TestCase):
    def test_summarize_and_filter(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "raw.csv"
            csv_path.write_text(
                "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n"
                "2026-01-01,s1,v1,1,100,1048576,200,ok,\n"
                "2026-01-01,s1,v1,2,200,1048576,300,ok,\n"
                "2026-01-01,s1,v2,1,-1,-1,-1,build_failed,x\n",
                encoding="utf-8",
            )
            all_rows = summarize_csv(csv_path)
            self.assertEqual(len(all_rows), 2)
            filtered = summarize_csv(csv_path, scenario="s1", variant="v1")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0].runs, 2)
            self.assertAlmostEqual(filtered[0].build_avg_ms or 0.0, 150.0)

    def test_missing_required_columns(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "raw.csv"
            csv_path.write_text("scenario,variant\ns1,v1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                summarize_csv(csv_path)

    def test_output_formatters(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            csv_path = Path(td) / "raw.csv"
            csv_path.write_text(
                "date,scenario,variant,run,build_ms,image_bytes,startup_ms,status,notes\n"
                "2026-01-01,s1,v1,1,100,1048576,200,ok,\n",
                encoding="utf-8",
            )
            summaries = summarize_csv(csv_path)
            table = format_table(summaries)
            data = format_json(summaries)
            self.assertIn("| Scenario | Variant |", table)
            self.assertIn('"scenario": "s1"', data)


if __name__ == "__main__":
    unittest.main()

