from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.config import load_config, resolve_benchmark_run_config


class ConfigTests(unittest.TestCase):
    def test_load_missing_config_returns_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            cfg = load_config(Path(td) / ".springdocker.toml")
            self.assertEqual(cfg, {})

    def test_resolve_benchmark_config_from_file(self) -> None:
        loaded = {
            "project": {"build_tool": "maven"},
            "benchmark": {"profile": "full", "runner_args": ["--skip-native"]},
        }
        resolved = resolve_benchmark_run_config(None, None, None, loaded)
        self.assertEqual(resolved.build_tool, "maven")
        self.assertEqual(resolved.profile, "full")
        self.assertEqual(resolved.runner_args, ["--skip-native"])

    def test_cli_overrides_config(self) -> None:
        loaded = {
            "project": {"build_tool": "maven"},
            "benchmark": {"profile": "full", "runner_args": ["--skip-native"]},
        }
        resolved = resolve_benchmark_run_config("gradle", "quick", ["--runs", "2"], loaded)
        self.assertEqual(resolved.build_tool, "gradle")
        self.assertEqual(resolved.profile, "quick")
        self.assertEqual(resolved.runner_args, ["--runs", "2"])


if __name__ == "__main__":
    unittest.main()

