"""
TOON (Token Optimized Object Notation) Converter

A Python library for converting JSON to TOON format, reducing token usage
by 40-60% when sending structured data to LLMs.

Author: Prashant Dudami
"""

from .converter import (
    TOONConverter,
    json_to_toon,
    toon_to_json,
)
from .exceptions import TOONConversionError, TOONParseError

__version__ = "1.0.0"
__all__ = [
    "TOONConverter",
    "json_to_toon",
    "toon_to_json",
    "TOONConversionError",
    "TOONParseError",
]
