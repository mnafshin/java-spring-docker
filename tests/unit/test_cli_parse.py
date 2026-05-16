from __future__ import annotations

import unittest

from tests.test_support import add_src_to_path

add_src_to_path()

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

    def test_inspect_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["inspect", "--format", "json"])
        self.assertEqual(args.command, "inspect")
        self.assertEqual(args.format, "json")
        self.assertEqual(args.project_root, ".")

    def test_explain_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["explain", "Dockerfile.generated", "--format", "json"])
        self.assertEqual(args.command, "explain")
        self.assertEqual(args.dockerfile, "Dockerfile.generated")
        self.assertEqual(args.format, "json")

    def test_compare_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args(["benchmark", "compare", "results/raw.csv", "--baseline-variant", "with-cache"])
        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.benchmark_command, "compare")
        self.assertEqual(args.raw_csv, "results/raw.csv")
        self.assertEqual(args.baseline_variant, "with-cache")

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
        args = parser.parse_args(["benchmark", "run", "--profile", "full", "--max-workers", "4"])
        self.assertEqual(args.command, "benchmark")
        self.assertEqual(args.benchmark_command, "run")
        self.assertEqual(args.profile, "full")
        self.assertEqual(args.max_workers, 4)

    def test_benchmark_run_parse_reproducibility_flags(self) -> None:
        parser = build_parser()
        args = parser.parse_args(
            [
                "benchmark",
                "run",
                "--cpuset-cpus",
                "0-1",
                "--memory",
                "2g",
                "--warmup-runs",
                "2",
                "--normalized-runtime",
            ]
        )
        self.assertEqual(args.cpuset_cpus, "0-1")
        self.assertEqual(args.memory, "2g")
        self.assertEqual(args.warmup_runs, 2)
        self.assertTrue(args.normalized_runtime)

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

    def test_benchmark_analyze_regression_parse(self) -> None:
        parser = build_parser()
        args = parser.parse_args([
            "benchmark",
            "analyze",
            "results/raw.csv",
            "--baseline",
            "baseline.json",
            "--fail-on-regression-above",
            "20",
        ])
        self.assertEqual(args.baseline, "baseline.json")
        self.assertEqual(args.fail_on_regression_above, 20.0)


if __name__ == "__main__":
    unittest.main()
