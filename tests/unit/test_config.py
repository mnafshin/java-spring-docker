from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.config import (
    load_config,
    resolve_benchmark_generate_config,
    resolve_benchmark_run_config,
    resolve_dockerfile_generate_config,
    resolve_doctor_config,
)


class ConfigTests(unittest.TestCase):
    def test_load_missing_config_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = load_config(Path(td) / ".springdocker.toml")
            self.assertEqual(cfg, {})

    def test_resolve_benchmark_config_from_file(self) -> None:
        loaded = {
            "project": {"build_tool": "maven"},
            "benchmark": {"run": {"profile": "full", "runner_args": ["--skip-native"], "legacy_scripts": True}},
        }
        resolved = resolve_benchmark_run_config(None, None, None, None, loaded)
        self.assertEqual(resolved.build_tool, "maven")
        self.assertEqual(resolved.profile, "full")
        self.assertEqual(resolved.runner_args, ["--skip-native"])
        self.assertTrue(resolved.use_legacy_scripts)

    def test_cli_overrides_config(self) -> None:
        loaded = {
            "project": {"build_tool": "maven"},
            "benchmark": {"run": {"profile": "full", "runner_args": ["--skip-native"]}},
        }
        resolved = resolve_benchmark_run_config("gradle", "quick", ["--runs", "2"], False, loaded)
        self.assertEqual(resolved.build_tool, "gradle")
        self.assertEqual(resolved.profile, "quick")
        self.assertEqual(resolved.runner_args, ["--runs", "2"])
        self.assertFalse(resolved.use_legacy_scripts)

    def test_resolve_other_command_configs(self) -> None:
        loaded = {
            "project": {"build_tool": "gradle"},
            "doctor": {"build_tool": "maven"},
            "dockerfile": {
                "output": "Dockerfile.ci",
                "java_version": 21,
                "must_have_modules_file": "must-have.txt",
                "legacy_scripts": True,
                "wizard_args": ["--profile", "balanced"],
            },
            "benchmark": {
                "generate": {"java_version": 21, "legacy_scripts": True},
            },
        }
        doctor = resolve_doctor_config(None, loaded)
        dockerfile = resolve_dockerfile_generate_config(None, None, None, None, None, loaded)
        bench_generate = resolve_benchmark_generate_config(None, None, None, loaded)
        self.assertEqual(doctor.build_tool, "maven")
        self.assertEqual(dockerfile.build_tool, "gradle")
        self.assertEqual(dockerfile.output, "Dockerfile.ci")
        self.assertEqual(dockerfile.java_version, 21)
        self.assertEqual(dockerfile.must_have_modules_file, "must-have.txt")
        self.assertTrue(dockerfile.use_legacy_scripts)
        self.assertEqual(bench_generate.java_version, 21)
        self.assertTrue(bench_generate.use_legacy_scripts)

    def test_strict_unknown_key_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = Path(td) / ".springdocker.toml"
            cfg.write_text("[project]\nbuild_tool='maven'\n[unknown]\na=1\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(cfg, strict=True)


if __name__ == "__main__":
    unittest.main()
