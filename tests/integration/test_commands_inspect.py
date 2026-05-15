from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.commands import cmd_inspect
from springdocker.errors import EXIT_OK


class InspectCommandTests(unittest.TestCase):
    def test_inspect_outputs_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text(
                "<project>"
                "<parent><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-parent</artifactId><version>4.0.1</version></parent>"
                "<properties><java.version>25</java.version></properties>"
                "<dependencies><dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency></dependencies>"
                "</project>",
                encoding="utf-8",
            )
            (root / ".springdocker.toml").write_text("[project]\n", encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = cmd_inspect(root, None, "json")
            self.assertEqual(code, EXIT_OK)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["build_tool"], "maven")
            self.assertEqual(payload["java_version"], 25)
            self.assertIn("org.springframework.boot:spring-boot-starter-web", payload["direct_dependencies"])

    def test_inspect_outputs_table(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "build.gradle").write_text("plugins { id 'org.springframework.boot' version '3.3.0' }\n", encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                code = cmd_inspect(root, None, "table")
            self.assertEqual(code, EXIT_OK)
            output = stdout.getvalue()
            self.assertIn("| Field | Value |", output)
            self.assertIn("3.3.0", output)


if __name__ == "__main__":
    unittest.main()
