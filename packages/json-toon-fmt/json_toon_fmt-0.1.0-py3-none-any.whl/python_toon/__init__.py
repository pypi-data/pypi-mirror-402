"""
TOON Python Library - Token-Oriented Object Notation encoding.

A pure Python library that converts Python data structures to TOON format,
achieving 30-60% token reduction compared to JSON.
"""

from typing import Any

from .constants import Delimiter, EncodeOptions
from .main import (
    CircularReferenceError,
    DatasetTooLargeError,
    NonSerializableError,
    ToonEncodingError,
)
from .types import jsonArray, jsonObject, jsonPrimitive, jsonData


# Public Function
def encode(data: Any, options: EncodeOptions | None = None) -> str:
    """
    Convert any JSON-serializable value to TOON format.

    Args:
        data: Any Python data structure to encode
        options: Optional encoding configuration

    Returns:
        TOON format string

    Raises:
        ToonEncodingError: If data cannot be encoded
        CircularReferenceError: If circular references detected
        DatasetTooLargeError: If data exceeds 10MB limit
    """
    from .main import ToonEncoder

    encoder = ToonEncoder(options or EncodeOptions())
    return encoder.encode(data)

__all__ = [
    "encode",
    "EncodeOptions",
    "Delimiter",
    "ToonEncodingError",
    "CircularReferenceError",
    "DatasetTooLargeError",
    "NonSerializableError",
    "jsonData",
    "jsonPrimitive",
    "jsonObject",
    "jsonArray",
]
