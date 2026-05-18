from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.services.verify_service import (
    VerifyContext,
    render_verify_json,
    render_verify_junit,
    render_verify_sarif,
    run_verification,
)


class _Completed:
    def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class VerifyServiceTests(unittest.TestCase):
    def test_run_verification_marks_missing_sbom_as_failed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dockerfile = root / "Dockerfile.generated"
            dockerfile.write_text("FROM scratch\n", encoding="utf-8")
            with patch("springdocker.services.verify_service.shutil.which", return_value=None):
                outcome = run_verification(
                    VerifyContext(
                        project_root=root,
                        dockerfile_path=dockerfile,
                        image=None,
                        smoke_url=None,
                    )
                )
            sbom = next(item for item in outcome.results if item.name == "sbom")
            self.assertEqual(sbom.status, "failed")
            self.assertTrue(outcome.failed)

    def test_run_verification_passes_sbom_when_file_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dockerfile = root / "Dockerfile.generated"
            dockerfile.write_text("FROM scratch\n", encoding="utf-8")
            (root / "sbom.spdx.json").write_text(json.dumps({"spdxVersion": "SPDX-2.3"}), encoding="utf-8")
            with patch("springdocker.services.verify_service.shutil.which", return_value=None):
                outcome = run_verification(
                    VerifyContext(
                        project_root=root,
                        dockerfile_path=dockerfile,
                        image=None,
                        smoke_url=None,
                    )
                )
            sbom = next(item for item in outcome.results if item.name == "sbom")
            self.assertEqual(sbom.status, "passed")
            self.assertFalse(outcome.failed)

    def test_run_verification_calls_tool_verifiers_when_present(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dockerfile = root / "Dockerfile.generated"
            dockerfile.write_text("FROM scratch\n", encoding="utf-8")
            (root / "sbom.spdx.json").write_text(json.dumps({"spdxVersion": "SPDX-2.3"}), encoding="utf-8")

            with (
                patch("springdocker.services.verify_service.shutil.which", return_value="/usr/bin/fake"),
                patch("springdocker.services.verify_service.subprocess.run", return_value=_Completed()),
            ):
                outcome = run_verification(
                    VerifyContext(
                        project_root=root,
                        dockerfile_path=dockerfile,
                        image="demo:latest",
                        smoke_url=None,
                    )
                )
            hadolint = next(item for item in outcome.results if item.name == "hadolint")
            trivy = next(item for item in outcome.results if item.name == "trivy")
            self.assertEqual(hadolint.status, "passed")
            self.assertEqual(trivy.status, "passed")

    def test_render_verify_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            dockerfile = root / "Dockerfile.generated"
            dockerfile.write_text("FROM scratch\n", encoding="utf-8")
            (root / "sbom.spdx.json").write_text(json.dumps({"spdxVersion": "SPDX-2.3"}), encoding="utf-8")
            with patch("springdocker.services.verify_service.shutil.which", return_value=None):
                outcome = run_verification(
                    VerifyContext(
                        project_root=root,
                        dockerfile_path=dockerfile,
                        image=None,
                        smoke_url=None,
                    )
                )
            self.assertIn('"overall": "passed"', render_verify_json(outcome))
            self.assertIn("<testsuite", render_verify_junit(outcome))
            self.assertIn('"version": "2.1.0"', render_verify_sarif(outcome))


if __name__ == "__main__":
    unittest.main()
