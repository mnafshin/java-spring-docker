from __future__ import annotations

import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.cli import build_parser


class CliParseTests(unittest.TestCase):
    def test_doctor_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        self.assertEqual(args.command, "doctor")

    def test_benchmark_run_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["benchmark", "run", "--profile", "full"])
        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.benchmark_command, "run")
        self.assertEqual(args.profile, "full")


if __name__ == "__main__":
    unittest.main()

