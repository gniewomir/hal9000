class VaultFmError(Exception):
    """Base error for vault tooling."""


class ParseError(VaultFmError):
    """Reserved for parse failures (e.g. legacy tooling)."""


class ValidationError(VaultFmError):
    """Contract violation."""


class EncodingError(VaultFmError):
    """File is not valid UTF-8."""
