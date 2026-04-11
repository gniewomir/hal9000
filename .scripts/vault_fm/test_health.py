from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from vault_fm.health import (
    _fix_missing_front_matter_blocks,
    _insert_default_front_matter_if_missing,
    _normalize_compose_layout,
    fix_vault,
)
from vault_fm.io import split_front_matter


class TestHealthFixMissingFm(unittest.TestCase):
    def test_insert_default_front_matter_if_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "topics/none.md"
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_text("# Title\n\nBody.\n", encoding="utf-8")
            self.assertTrue(_insert_default_front_matter_if_missing(root, rel))
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            sp = split_front_matter(text, raw)
            self.assertTrue(sp.has_fm)
            self.assertTrue(text.startswith("---\n"))
            self.assertIn("id:", text)
            self.assertIn("references: []", text)
            self.assertIn("# Title", text)
            self.assertFalse(_insert_default_front_matter_if_missing(root, rel))

    def test_fix_missing_front_matter_blocks_uses_git_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "topics/none.md"
            (root / "topics").mkdir(parents=True)
            (root / rel).write_text("# x\n", encoding="utf-8")
            with patch("vault_fm.health.list_tracked_md", return_value=[rel]):
                _fix_missing_front_matter_blocks(root)
            text = (root / rel).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))

    def test_fix_vault_inserts_fm_when_patched_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "topics/none.md"
            (root / "topics").mkdir(parents=True)
            (root / rel).write_text("# x\n", encoding="utf-8")

            def fake_list(_repo: Path) -> list[str]:
                return [rel]

            with patch("vault_fm.health.list_tracked_md", side_effect=fake_list):
                fix_vault(root)
            text = (root / rel).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))

    def test_normalize_compose_layout_adds_newline_after_fence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "topics/spacing.md"
            (root / "topics").mkdir(parents=True)
            u = uuid.uuid7()
            raw = f"---\nid: {u}\nreferences: []\n---\n# Body\n".encode("utf-8")
            (root / rel).write_bytes(raw)
            with patch("vault_fm.health.list_tracked_md", return_value=[rel]):
                _normalize_compose_layout(root)
            out = (root / rel).read_bytes()
            self.assertIn(b"---\n\n# Body\n", out)

    def test_normalize_compose_layout_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            rel = "topics/ok.md"
            (root / "topics").mkdir(parents=True)
            u = uuid.uuid7()
            raw = f"---\nid: {u}\nreferences: []\n---\n\n# Body\n".encode("utf-8")
            (root / rel).write_bytes(raw)
            with patch("vault_fm.health.list_tracked_md", return_value=[rel]):
                _normalize_compose_layout(root)
                first = (root / rel).read_bytes()
                _normalize_compose_layout(root)
                second = (root / rel).read_bytes()
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
