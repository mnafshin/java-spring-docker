from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.benchmarks.generate import (
    NativeScenarioDefinition,
    StandardScenarioDefinition,
    default_scenarios,
    generate_benchmark_assets,
)


class GenerateScenarioTests(unittest.TestCase):
    def test_default_scenarios_use_explicit_native_type(self) -> None:
        scenarios = default_scenarios(build_tool="maven", java_version=21)
        native = next(item for item in scenarios if item.id == "07-native-vs-jvm")
        self.assertIsInstance(native, NativeScenarioDefinition)

    def test_standard_scenario_rejects_empty_variants(self) -> None:
        with self.assertRaises(ValueError):
            StandardScenarioDefinition(id="bad", variants=())

    def test_generate_assets_writes_standard_variants_and_keeps_native_folder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            generate_benchmark_assets(project_root=root, build_tool="maven", java_version=21)
            standard_variant = root / "benchmarks" / "01-multi-stage-build-structure" / "variants" / "specialized-multi-stage" / "Dockerfile"
            self.assertTrue(standard_variant.exists())
            native_dir = root / "benchmarks" / "07-native-vs-jvm" / "variants"
            self.assertTrue(native_dir.exists())


if __name__ == "__main__":
    unittest.main()
