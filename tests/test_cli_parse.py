from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.cli import build_parser


class CliParseTests(unittest.TestCase):
    def test_init_parse_profile_and_print(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["init", "--profile", "full", "--print"])
        self.assertEqual(args.command, "init")
        self.assertEqual(args.profile, "full")
        self.assertTrue(args.print_only)

    def test_doctor_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["doctor"])
        self.assertEqual(args.command, "doctor")

    def test_dockerfile_generate_parse_internal_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            ["dockerfile", "generate", "--output", "Dockerfile.prod", "--java-version", "21", "--use-legacy-scripts"]
        )
        self.assertEqual(args.command, "dockerfile")
        self.assertEqual(args.dockerfile_command, "generate")
        self.assertEqual(args.output, "Dockerfile.prod")
        self.assertEqual(args.java_version, 21)
        self.assertTrue(args.use_legacy_scripts)

    def test_benchmark_run_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["benchmark", "run", "--profile", "full"])
        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.benchmark_command, "run")
        self.assertEqual(args.profile, "full")

    def test_benchmark_analyze_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "benchmark",
            "analyze",
            "results/raw.csv",
            "--format",
            "json",
            "--scenario",
            "04-jep483-aot-cache",
            "--variant",
            "with-aot-cache",
            "--output",
            "out.json",
            "--fail-on-success-rate-below",
            "99.5",
        ])
        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.benchmark_command, "analyze")
        self.assertEqual(args.format, "json")
        self.assertEqual(args.scenario, "04-jep483-aot-cache")
        self.assertEqual(args.variant, "with-aot-cache")
        self.assertEqual(args.output, "out.json")
        self.assertEqual(args.fail_on_success_rate_below, 99.5)


if __name__ == "__main__":
    unittest.main()
