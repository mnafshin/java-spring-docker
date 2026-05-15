from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.project_detect import detect_build_tool, has_spring_project_markers, inspect_project_details


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

    def test_inspect_details_maven_namespace_and_reflection(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text(
                '<project xmlns="http://maven.apache.org/POM/4.0.0">'
                "<modelVersion>4.0.0</modelVersion>"
                "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId><version>4.0.1</version></parent>"
                "<properties><java.version>25</java.version></properties>"
                "<dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies>"
                "</project>",
                encoding="utf-8",
            )
            src = root / "src" / "main" / "java"
            src.mkdir(parents=True)
            (src / "Demo.java").write_text(
                "class Demo { void x() throws Exception { Class.forName(\"x\"); } }\n",
                encoding="utf-8",
            )
            info = inspect_project_details(root)
            self.assertEqual(info.java_version, 25)
            self.assertEqual(info.spring_boot_version, "4.0.1")
            self.assertIn("org.springframework.boot:spring-boot-starter-web", info.direct_dependencies)
            self.assertEqual(info.runtime_compatibility, "compatible")
            self.assertTrue(info.reflection_hits)

    def test_inspect_details_gradle(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build.gradle").write_text(
                "plugins { id 'org.springframework.boot' version '3.3.0' }\n"
                "java { toolchain { languageVersion = JavaLanguageVersion.of(17) } }\n"
                "dependencies { implementation 'org.springframework.boot:spring-boot-starter-web:3.3.0' }\n",
                encoding="utf-8",
            )
            info = inspect_project_details(root)
            self.assertEqual(info.java_version, 17)
            self.assertEqual(info.spring_boot_version, "3.3.0")
            self.assertIn("org.springframework.boot:spring-boot-starter-web", info.direct_dependencies)
            self.assertEqual(info.runtime_compatibility, "compatible")


if __name__ == "__main__":
    unittest.main()
