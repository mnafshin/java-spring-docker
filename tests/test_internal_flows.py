from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.commands import cmd_benchmark_generate, cmd_benchmark_run, cmd_dockerfile_generate


class _FakeCompleted:
    def __init__(self, returncode: int = 0, stdout: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout


class InternalFlowTests(unittest.TestCase):
    def test_dockerfile_generate_without_legacy_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            code = cmd_dockerfile_generate(
                project_root=root,
                build_tool=None,
                output="Dockerfile.generated",
                java_version=21,
                extra_args=[],
                use_legacy_scripts=False,
            )
            self.assertEqual(code, 0)
            self.assertTrue((root / "Dockerfile.generated").exists())

    def test_benchmark_generate_without_legacy_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            code = cmd_benchmark_generate(
                project_root=root,
                build_tool=None,
                java_version=25,
                use_legacy_scripts=False,
            )
            self.assertEqual(code, 0)
            self.assertTrue((root / "benchmarks" / "01-base-image-pinning" / "variants").exists())

    def test_benchmark_run_without_legacy_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            cmd_benchmark_generate(project_root=root, build_tool=None, java_version=25, use_legacy_scripts=False)

            def fake_run(args, **kwargs):  # type: ignore[no-untyped-def]
                if args[:3] == ["docker", "image", "inspect"]:
                    return _FakeCompleted(stdout="1048576")
                return _FakeCompleted(returncode=0, stdout="")

            with patch("springdocker.benchmarks.runner._wait_readiness", return_value=100), patch(
                "springdocker.benchmarks.runner.subprocess.run", side_effect=fake_run
            ):
                code = cmd_benchmark_run(
                    project_root=root,
                    build_tool=None,
                    profile="quick",
                    extra_args=["--runs", "1", "--skip-native"],
                    use_legacy_scripts=False,
                )
            self.assertEqual(code, 0)
            raw_csv = root / "benchmarks" / "01-base-image-pinning" / "results" / "raw.csv"
            self.assertTrue(raw_csv.exists())
            self.assertIn("01-base-image-pinning", raw_csv.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

