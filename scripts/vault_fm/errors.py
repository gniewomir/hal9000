class VaultFmError(Exception):
    """Base error for vault front matter tooling."""


class ParseError(VaultFmError):
    """Front matter or YAML subset parse failure."""


class ValidationError(VaultFmError):
    """Contract violation (append-only, invalid UUID, etc.)."""


class EncodingError(VaultFmError):
    """File is not valid UTF-8."""
