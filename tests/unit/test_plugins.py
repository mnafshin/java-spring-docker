from __future__ import annotations

import unittest
from unittest.mock import patch

from tests.test_support import add_src_to_path

add_src_to_path()

from springdocker.dockerfile import DockerfileOptions
from springdocker.plugins import apply_dockerfile_mutators


class _EntryPoint:
    def __init__(self, name: str, loaded) -> None:  # type: ignore[no-untyped-def]
        self.name = name
        self._loaded = loaded

    def load(self):  # type: ignore[no-untyped-def]
        return self._loaded


class _AppendingPlugin:
    name = "append-label"

    def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str:
        return dockerfile_text + f'\nLABEL org.example.java="{options.java_version}"\n'


class _FailingPlugin:
    name = "broken-plugin"

    def mutate_dockerfile(self, dockerfile_text: str, options: DockerfileOptions) -> str:
        raise RuntimeError("boom")


class PluginTests(unittest.TestCase):
    def test_applies_discovered_mutator(self) -> None:
        options = DockerfileOptions(build_tool="maven", java_version=21)
        with patch("springdocker.plugins._iter_entry_points", return_value=[_EntryPoint("append-label", _AppendingPlugin)]):
            result = apply_dockerfile_mutators("FROM base\n", options)
        self.assertIn('LABEL org.example.java="21"', result.dockerfile_text)
        self.assertEqual(result.warnings, ())

    def test_isolates_plugin_failures(self) -> None:
        options = DockerfileOptions(build_tool="maven")
        with patch("springdocker.plugins._iter_entry_points", return_value=[_EntryPoint("broken", _FailingPlugin)]):
            result = apply_dockerfile_mutators("FROM base\n", options)
        self.assertEqual(result.dockerfile_text, "FROM base\n")
        self.assertIn("plugin 'broken' failed", result.warnings[0])


if __name__ == "__main__":
    unittest.main()

