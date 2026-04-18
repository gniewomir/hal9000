from __future__ import annotations

from pathlib import Path

from vault_fm.errors import EncodingError

BOM = b"\xef\xbb\xbf"


def read_file_utf8(path: Path) -> tuple[str, bytes]:
    """Read file as strict UTF-8. Returns (text without BOM prefix, raw bytes without BOM)."""
    raw = path.read_bytes()
    if raw.startswith(BOM):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        raise EncodingError(f"{path}: invalid UTF-8: {e}") from e
    return text, raw
