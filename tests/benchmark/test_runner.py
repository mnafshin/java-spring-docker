from __future__ import annotations

import unittest

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.benchmarks.runner import _runtime_flags


class RunnerTests(unittest.TestCase):
    def test_runtime_flags_include_isolation_controls(self) -> None:
        self.assertEqual(
            _runtime_flags("0-1", "2g", True),
            [
                "--cpuset-cpus",
                "0-1",
                "--memory",
                "2g",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges",
                "--tmpfs",
                "/tmp",
            ],
        )

    def test_runtime_flags_empty_when_disabled(self) -> None:
        self.assertEqual(_runtime_flags(None, None, False), [])


if __name__ == "__main__":
    unittest.main()
