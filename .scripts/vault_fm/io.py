from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from vault_fm.errors import EncodingError, ParseError


@dataclass
class SplitFrontMatter:
    """Result of splitting a markdown file."""

    has_fm: bool
    fm_text: str | None
    body_bytes: bytes


BOM = b"\xef\xbb\xbf"


def read_file_utf8(path: Path) -> tuple[str, bytes]:
    """Read file as strict UTF-8. Returns (text without BOM prefix for FM logic, raw bytes)."""
    raw = path.read_bytes()
    if raw.startswith(BOM):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise EncodingError(f"{path}: invalid UTF-8: {e}") from e
    return text, raw


def split_front_matter(text: str, raw_without_bom: bytes) -> SplitFrontMatter:
    """
    Split first --- ... --- block. raw_without_bom is bytes corresponding to `text`
    (no BOM). Body bytes are a slice of raw_without_bom so line endings are preserved.
    """
    lines = text.splitlines(keepends=True)
    if not lines:
        return SplitFrontMatter(False, None, raw_without_bom)

    if lines[0].strip() != "---":
        return SplitFrontMatter(False, None, raw_without_bom)

    close_idx: int | None = None
    for j in range(1, len(lines)):
        if lines[j].strip() == "---":
            close_idx = j
            break
    if close_idx is None:
        raise ParseError("unclosed front matter block (missing closing ---)")

    fm_text = "".join(lines[1:close_idx])
    prefix = "".join(lines[: close_idx + 1])
    prefix_bytes = prefix.encode("utf-8")
    body_bytes = raw_without_bom[len(prefix_bytes) :]
    return SplitFrontMatter(True, fm_text, body_bytes)


def compose_front_matter(fm_text: str, body_bytes: bytes) -> bytes:
    """
    Wrap fm_text with --- delimiters and append body bytes.

    The inner YAML must end with a newline before the closing delimiter so the
    fence is not glued to the last key. After the closing --- line, emit a newline
    before the body; if the body does not already start with a line break, insert
    one so the first body line is separated from the fence (a blank line when the
    body had no leading newline).
    """
    inner = fm_text if (not fm_text or fm_text.endswith("\n")) else fm_text + "\n"
    block = f"---\n{inner}---\n".encode("utf-8")
    if not body_bytes:
        return block
    if not body_bytes.startswith(b"\n") and not body_bytes.startswith(b"\r\n"):
        block += b"\n"
    return block + body_bytes


def default_fm_text(note_id: str) -> str:
    """Canonical new block text between delimiters (includes trailing newline before ---)."""
    return f"id: {note_id}\nreferences: []\n"
