from __future__ import annotations

import unittest
import uuid

from vault_fm.errors import ParseError
from vault_fm.io import compose_front_matter, default_fm_text, split_front_matter
from vault_fm.parse import (
    find_matching_bracket,
    parse_fm_inner,
    rebuild_fm_canonical,
    split_flow_list_inner,
)
from vault_fm.paths import is_in_scope


class TestFlowBracket(unittest.TestCase):
    def test_matching(self) -> None:
        s = "[a, b, c]"
        self.assertEqual(find_matching_bracket(s, 0), len(s) - 1)

    def test_quotes(self) -> None:
        s = '["a,b", c]'
        self.assertEqual(find_matching_bracket(s, 0), len(s) - 1)


class TestParseFm(unittest.TestCase):
    def test_roundtrip_default(self) -> None:
        u = uuid.uuid7()
        fm = default_fm_text(str(u))
        p = parse_fm_inner(fm)
        self.assertEqual(p.id_val, u)
        self.assertEqual(p.refs_parsed, [])
        self.assertTrue(p.has_id_key and p.has_references_key)

    def test_block_refs(self) -> None:
        a = uuid.uuid7()
        b = uuid.uuid7()
        fm = f"id: {a}\nreferences:\n  - {b}\n"
        p = parse_fm_inner(fm)
        self.assertEqual(p.refs_parsed, [b])

    def test_flow_refs(self) -> None:
        a = uuid.uuid7()
        b = uuid.uuid7()
        c = uuid.uuid7()
        fm = f"id: {a}\nreferences: [{b}, {c}]\n"
        p = parse_fm_inner(fm)
        self.assertEqual(p.refs_parsed, [b, c])

    def test_dup_keys(self) -> None:
        u = uuid.uuid7()
        fm = f"id: {u}\nid: {u}\nreferences: []\n"
        with self.assertRaises(ParseError):
            parse_fm_inner(fm)

    def test_wrong_case(self) -> None:
        u = uuid.uuid7()
        fm = f"Id: {u}\nreferences: []\n"
        with self.assertRaises(ParseError):
            parse_fm_inner(fm)

    def test_rebuild(self) -> None:
        u = uuid.uuid7()
        v = uuid.uuid7()
        w = uuid.uuid7()
        fm = f"id: {u}\nreferences: [{u}]\n"
        p = parse_fm_inner(fm)
        out = rebuild_fm_canonical(fm, u, [v, w])
        p2 = parse_fm_inner(out)
        self.assertEqual(p2.refs_parsed, [v, w])


class TestSplitFm(unittest.TestCase):
    def test_no_fm(self) -> None:
        raw = b"hello\n"
        sp = split_front_matter(raw.decode(), raw)
        self.assertFalse(sp.has_fm)


class TestComposeFm(unittest.TestCase):
    def test_newline_after_fence_when_body_has_no_leading_break(self) -> None:
        u = uuid.uuid7()
        fm = default_fm_text(str(u))
        out = compose_front_matter(fm, b"# Title\n")
        self.assertIn(b"---\n", out)
        self.assertTrue(out.startswith(b"---\n"))
        # Blank line between closing --- and body when body did not start with \n
        self.assertIn(b"---\n\n# Title\n", out)

    def test_no_extra_blank_when_body_already_starts_with_newline(self) -> None:
        u = uuid.uuid7()
        fm = default_fm_text(str(u))
        out = compose_front_matter(fm, b"\n# Title\n")
        self.assertNotIn(b"---\n\n\n#", out)
        self.assertIn(b"---\n\n# Title\n", out)

    def test_roundtrip_split_preserves_compose_blank_line_rule(self) -> None:
        u = uuid.uuid7()
        fm = default_fm_text(str(u))
        raw = compose_front_matter(fm, b"# x\n")
        sp = split_front_matter(raw.decode("utf-8"), raw)
        self.assertTrue(sp.has_fm)
        raw2 = compose_front_matter(sp.fm_text or "", sp.body_bytes)
        self.assertEqual(raw, raw2)


class TestIsInScope(unittest.TestCase):
    def test_cursor_excluded(self) -> None:
        self.assertFalse(is_in_scope(".cursor/rules/note.md"))

    def test_vault_note_included(self) -> None:
        self.assertTrue(is_in_scope("topics/foo/bar.md"))


if __name__ == "__main__":
    unittest.main()
