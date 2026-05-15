from __future__ import annotations

import unittest

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.analyze import VariantSummary
from springdocker.compare import compare_summaries, format_delta_json, format_delta_table


class CompareTests(unittest.TestCase):
    def test_compare_against_baseline(self) -> None:
        summaries = [
            VariantSummary("s1", "baseline", 2, 100.0, 200.0, 220.0, 100.0, 100.0),
            VariantSummary("s1", "tuned", 2, 80.0, 180.0, 200.0, 90.0, 100.0),
        ]
        deltas = compare_summaries("baseline", summaries)
        self.assertEqual(len(deltas), 2)
        self.assertTrue(deltas[0].is_baseline)
        self.assertAlmostEqual(deltas[1].build_delta_ms or 0.0, -20.0)
        self.assertAlmostEqual(deltas[1].startup_delta_pct or 0.0, -10.0)
        self.assertIn("baseline", format_delta_table(deltas))
        self.assertIn('"variant": "tuned"', format_delta_json(deltas))

    def test_missing_baseline_fails(self) -> None:
        summaries = [VariantSummary("s1", "other", 1, 1.0, 1.0, 1.0, 1.0, 100.0)]
        with self.assertRaises(ValueError):
            compare_summaries("baseline", summaries)

    def test_single_variant_is_baseline(self) -> None:
        summaries = [VariantSummary("s1", "baseline", 1, 1.0, 1.0, 1.0, 1.0, 100.0)]
        deltas = compare_summaries("baseline", summaries)
        self.assertEqual(len(deltas), 1)
        self.assertTrue(deltas[0].is_baseline)


if __name__ == "__main__":
    unittest.main()
