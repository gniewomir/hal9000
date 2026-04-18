from __future__ import annotations

import unittest

from vault_fm.gitutil import _parse_name_status_z
from vault_fm.links import (
    canonical_rel_link,
    legacy_logical_target_rel,
    rewrite_note_body_links,
    split_path_and_suffix,
)
from vault_fm.rename_links import _make_canonical_replace_dest, _make_replace_dest


class TestParseNameStatusZ(unittest.TestCase):
    def test_rename_pair(self) -> None:
        b = b"M\x00a.md\x00R100\x00old/x.md\x00new/y.md\x00"
        self.assertEqual(
            _parse_name_status_z(b),
            [("old/x.md", "new/y.md")],
        )

    def test_copy_pair(self) -> None:
        b = b"C089\x00src.md\x00dst.md\x00"
        self.assertEqual(
            _parse_name_status_z(b),
            [("src.md", "dst.md")],
        )

    def test_modify_only_no_renames(self) -> None:
        b = b"M\x00a.md\x00A\x00b.md\x00"
        self.assertEqual(_parse_name_status_z(b), [])


class TestSplitPathAndSuffix(unittest.TestCase):
    def test_hash(self) -> None:
        self.assertEqual(
            split_path_and_suffix("a.md#sec"),
            ("a.md", "#sec"),
        )

    def test_query_and_hash(self) -> None:
        self.assertEqual(
            split_path_and_suffix("a.md?q=1#h"),
            ("a.md", "?q=1#h"),
        )


class TestLegacyLogical(unittest.TestCase):
    def test_up(self) -> None:
        self.assertEqual(
            legacy_logical_target_rel("vault/a/b.md", "../c.md"),
            "vault/c.md",
        )

    def test_leading_slash(self) -> None:
        self.assertEqual(
            legacy_logical_target_rel("vault/a/b.md", "/vault/z.md"),
            "vault/z.md",
        )


class TestCanonicalReplaceDest(unittest.TestCase):
    def test_rewrites_relative(self) -> None:
        tracked = frozenset({"vault/c.md"})
        fn = _make_canonical_replace_dest("vault/a/b.md", tracked)
        self.assertEqual(fn("../c.md"), "vault/c.md")

    def test_strips_leading_slash(self) -> None:
        tracked = frozenset({"vault/z.md"})
        fn = _make_canonical_replace_dest("vault/a/b.md", tracked)
        self.assertEqual(fn("/vault/z.md"), "vault/z.md")

    def test_skips_already_canonical(self) -> None:
        tracked = frozenset({"vault/z.md"})
        fn = _make_canonical_replace_dest("vault/a/b.md", tracked)
        self.assertIsNone(fn("vault/z.md"))


class TestCanonicalRelLink(unittest.TestCase):
    def test_sibling(self) -> None:
        self.assertEqual(
            canonical_rel_link("vault/topics/a/x.md", "vault/topics/a/y.md"),
            "y.md",
        )

    def test_up_and_over(self) -> None:
        self.assertEqual(
            canonical_rel_link("vault/topics/a/x.md", "vault/topics/b/z.md"),
            "../b/z.md",
        )


class TestMakeReplaceDest(unittest.TestCase):
    def test_rewrites_matching_target(self) -> None:
        rename = {"vault/old.md": "vault/new.md"}
        fn = _make_replace_dest("vault/topics/a/x.md", rename)
        self.assertEqual(fn("vault/old.md#h"), "vault/new.md#h")

    def test_skips_non_matching(self) -> None:
        rename = {"vault/old.md": "vault/new.md"}
        fn = _make_replace_dest("vault/topics/a/x.md", rename)
        self.assertIsNone(fn("vault/other.md"))


class TestRewriteNoteBodyLinks(unittest.TestCase):
    def test_inline_preserves_fragment(self) -> None:
        rename = {"vault/old.md": "vault/new.md"}
        fn = _make_replace_dest("vault/topics/a/x.md", rename)
        body = "See [t](vault/old.md#h)\n"
        out = rewrite_note_body_links("vault/topics/a/x.md", body, fn)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertIn("vault/new.md#h", out)
        self.assertNotIn("vault/old.md", out)

    def test_ref_definition_rewritten(self) -> None:
        rename = {"vault/tgt.md": "vault/renamed.md"}
        fn = _make_replace_dest("vault/a/note.md", rename)
        body = "[x]: vault/tgt.md\n\nLink [text][x]\n"
        out = rewrite_note_body_links("vault/a/note.md", body, fn)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertIn("vault/renamed.md", out)
        self.assertNotIn("vault/tgt.md", out)

    def test_canonical_rewrites_body_relative(self) -> None:
        tracked = frozenset({"vault/tgt.md"})
        fn = _make_canonical_replace_dest("vault/a/note.md", tracked)
        body = "See [x](../tgt.md)\n"
        out = rewrite_note_body_links("vault/a/note.md", body, fn)
        self.assertIsNotNone(out)
        assert out is not None
        self.assertIn("](vault/tgt.md)", out)


if __name__ == "__main__":
    unittest.main()
