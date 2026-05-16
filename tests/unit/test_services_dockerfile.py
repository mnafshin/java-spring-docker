from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.services.dockerfile_service import generate_dockerfile, parse_must_have_modules


class DockerfileServiceTests(unittest.TestCase):
    def test_parse_must_have_modules_deduplicates_and_strips_comments(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            modules_file = root / "modules.txt"
            modules_file.write_text(
                "java.sql, java.naming\n"
                "java.naming # duplicate\n"
                "java.management\n",
                encoding="utf-8",
            )
            parsed = parse_must_have_modules(root, "modules.txt")
            self.assertEqual(parsed, ("java.sql", "java.naming", "java.management"))

    def test_parse_must_have_modules_rejects_invalid_name(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            modules_file = root / "modules.txt"
            modules_file.write_text("java.base\nbad module\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                parse_must_have_modules(root, "modules.txt")

    def test_generate_dockerfile_creates_parent_directories(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            destination = generate_dockerfile(
                project_root=root,
                output_path="nested/Dockerfile.generated",
                build_tool="maven",
                java_version=21,
                must_have_modules_file=None,
            )
            self.assertTrue(destination.exists())
            self.assertIn("FROM --platform=$BUILDPLATFORM eclipse-temurin:21-jdk AS build", destination.read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()

