from __future__ import annotations

import unittest
from pathlib import Path

from vault_fm.links import (
    _check_one_path,
    _iter_body_lines_outside_fences,
    _should_skip_destination,
    logical_target_rel,
    validate_note_body_links,
)


class TestSkipAndLogical(unittest.TestCase):
    def test_skip_http(self) -> None:
        self.assertTrue(_should_skip_destination("https://a.com/x.md"))

    def test_skip_empty_fragment(self) -> None:
        self.assertTrue(_should_skip_destination("#x"))

    def test_relative_not_skipped(self) -> None:
        self.assertFalse(_should_skip_destination("./x.png"))

    def test_logical_relative(self) -> None:
        self.assertEqual(
            logical_target_rel("topics/a/b.md", "c.md"),
            "topics/a/c.md",
        )

    def test_logical_up(self) -> None:
        self.assertEqual(
            logical_target_rel("topics/a/b.md", "../c.md"),
            "topics/c.md",
        )

    def test_logical_root_slash(self) -> None:
        self.assertEqual(
            logical_target_rel("topics/a/b.md", "/README.md"),
            "README.md",
        )


class TestFences(unittest.TestCase):
    def test_fence_hides_line(self) -> None:
        body = "```\n[bad](missing.png)\n```\n\n[ok](topics/x.md)\n"
        lines = _iter_body_lines_outside_fences(body)
        joined = "\n".join(ln for _n, ln in lines)
        self.assertNotIn("missing", joined)
        self.assertIn("[ok](topics/x.md)", joined)


class TestValidateBody(unittest.TestCase):
    def test_missing_target(self) -> None:
        tracked = frozenset({"topics/a.md"})
        issues = validate_note_body_links(
            Path("/repo"),
            "topics/a.md",
            "see [x](nope.png)",
            tracked,
        )
        self.assertTrue(any("broken link" in x for x in issues))

    def test_tracked_ok(self) -> None:
        root = Path(__file__).resolve().parents[2]
        rel = ".scripts/vault_fm/test_links.py"
        tracked = frozenset({rel, ".scripts/vault_fm/parse.py"})
        issues = validate_note_body_links(
            root,
            rel,
            "see [p](parse.py)",
            tracked,
        )
        self.assertEqual(issues, [])


class TestCheckOnePath(unittest.TestCase):
    def test_tracked_regular_file(self) -> None:
        root = Path(__file__).resolve().parents[2]
        rel_self = ".scripts/vault_fm/test_links.py"
        tracked = frozenset({rel_self, ".scripts/vault_fm/parse.py"})
        err = _check_one_path(root, rel_self, "parse.py", tracked)
        self.assertIsNone(err)
