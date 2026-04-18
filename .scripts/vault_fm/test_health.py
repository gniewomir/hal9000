from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vault_fm import health


class TestHealthMain(unittest.TestCase):
    def test_fix_runs_rename_repair(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("vault_fm.health.git_repo_root", return_value=root):
                with patch(
                    "vault_fm.health.run_link_validation_with_rename_repair",
                    return_value=[],
                ) as m:
                    r = health.main(["--fix"])
            self.assertEqual(r, 0)
            m.assert_called_once_with(root)

    def test_no_fix_validates_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("vault_fm.health.git_repo_root", return_value=root):
                with patch(
                    "vault_fm.health.validate_tracked_links",
                    return_value=[],
                ) as m:
                    r = health.main([])
            self.assertEqual(r, 0)
            m.assert_called_once_with(root)

    def test_nonzero_on_issues(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch("vault_fm.health.git_repo_root", return_value=root):
                with patch(
                    "vault_fm.health.validate_tracked_links",
                    return_value=["vault/x.md:1:1: broken"],
                ):
                    with patch("builtins.print"):
                        r = health.main([])
            self.assertEqual(r, 1)


if __name__ == "__main__":
    unittest.main()
