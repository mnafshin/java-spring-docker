from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from springdocker.commands import cmd_init


class InitCommandTests(unittest.TestCase):
    def test_init_writes_config(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            cfg = root / ".springdocker.toml"
            code = cmd_init(root, None, cfg, force=False)
            self.assertEqual(code, 0)
            self.assertTrue(cfg.exists())
            text = cfg.read_text(encoding="utf-8")
            self.assertIn('build_tool = "maven"', text)

    def test_init_requires_force_when_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "pom.xml").write_text("<project/>", encoding="utf-8")
            cfg = root / ".springdocker.toml"
            cfg.write_text("[project]\n", encoding="utf-8")
            code = cmd_init(root, None, cfg, force=False)
            self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

