from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from shutil import copytree
from unittest.mock import patch

from springdocker.cli import main

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"


class _FakeCompleted:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class CliIntegrationTests(unittest.TestCase):
    def _workspace_from_fixture(self, name: str) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        td = tempfile.TemporaryDirectory()
        root = Path(td.name) / "project"
        copytree(FIXTURES / name, root)
        return td, root

    def test_doctor_detects_maven_fixture(self) -> None:
        td, project = self._workspace_from_fixture("maven-only")
        self.addCleanup(td.cleanup)
        code = main(["doctor", "--project-root", str(project)])
        self.assertEqual(code, 0)

    def test_doctor_requires_build_tool_for_mixed_markers(self) -> None:
        td, project = self._workspace_from_fixture("mixed-markers")
        self.addCleanup(td.cleanup)
        self.assertEqual(main(["doctor", "--project-root", str(project)]), 2)
        self.assertEqual(main(["doctor", "--project-root", str(project), "--build-tool", "gradle"]), 0)

    def test_generate_and_run_with_internal_paths(self) -> None:
        td, project = self._workspace_from_fixture("gradle-only")
        self.addCleanup(td.cleanup)

        self.assertEqual(
            main(["dockerfile", "generate", "--project-root", str(project), "--output", "Dockerfile.test"]),
            0,
        )
        self.assertTrue((project / "Dockerfile.test").exists())
        self.assertEqual(main(["benchmark", "generate", "--project-root", str(project)]), 0)

        def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
            if args[:3] == ["docker", "image", "inspect"]:
                return _FakeCompleted(stdout="1048576")
            return _FakeCompleted(returncode=0, stdout="")

        with patch("springdocker.benchmarks.runner._wait_readiness", return_value=100), patch(
            "springdocker.benchmarks.runner.subprocess.run", side_effect=fake_run
        ):
            code = main(
                [
                    "benchmark",
                    "run",
                    "--project-root",
                    str(project),
                    "--profile",
                    "quick",
                    "--runner-arg=--runs",
                    "--runner-arg=1",
                    "--runner-arg=--skip-native",
                ]
            )
        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
