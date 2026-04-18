from __future__ import annotations

import unittest

from vault_fm.paths import is_in_scope


class TestIsInScope(unittest.TestCase):
    def test_cursor_excluded(self) -> None:
        self.assertFalse(is_in_scope(".cursor/rules/note.md"))

    def test_vault_note_included(self) -> None:
        self.assertTrue(is_in_scope("topics/foo/bar.md"))


if __name__ == "__main__":
    unittest.main()
