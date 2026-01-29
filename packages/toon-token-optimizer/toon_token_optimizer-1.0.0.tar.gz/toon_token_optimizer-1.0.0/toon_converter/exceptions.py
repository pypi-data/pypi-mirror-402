"""
Custom exceptions for TOON converter.
"""


class TOONConversionError(Exception):
    """Raised when JSON to TOON conversion fails."""

    pass


class TOONParseError(Exception):
    """Raised when TOON to JSON parsing fails."""

    pass
