from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.project_detect import detect_build_tool, has_spring_project_markers


class ProjectDetectTests(unittest.TestCase):
    def test_detect_maven(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            self.assertEqual(detect_build_tool(root), "maven")

    def test_detect_gradle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
            self.assertEqual(detect_build_tool(root), "gradle")

    def test_detect_ambiguous_requires_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            (root / "gradlew").write_text("#!/bin/sh\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                detect_build_tool(root)
            self.assertEqual(detect_build_tool(root, "maven"), "maven")

    def test_spring_markers(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            app_props = root / "src" / "main" / "resources"
            app_props.mkdir(parents=True)
            (app_props / "application.properties").write_text("spring.application.name=x\n", encoding="utf-8")
            self.assertTrue(has_spring_project_markers(root))


if __name__ == "__main__":
    unittest.main()

