"""
TOON (Token Optimized Object Notation) Converter

Converts JSON arrays to TOON format for token-efficient LLM communication.
TOON separates schema from data, reducing redundant attribute name repetition.

Example:
    JSON:
    [
        {"name": "John", "age": 30, "city": "NYC"},
        {"name": "Jane", "age": 25, "city": "LA"}
    ]

    TOON:
    @schema:name,age,city
    John|30|NYC
    Jane|25|LA
"""

from typing import Any, Optional
from .exceptions import TOONConversionError, TOONParseError


class TOONConverter:
    """
    Converts between JSON and TOON formats.
    
    TOON Format Specification:
    - Schema line starts with '@schema:' followed by comma-separated attribute names
    - Data rows use '|' as the value delimiter
    - Empty/null values are represented as empty strings between delimiters
    - Pipe characters in values are escaped as '\\|'
    - Nested objects are flattened using dot notation (e.g., 'address.city')
    - Arrays within fields are serialized as comma-separated values
    """

    SCHEMA_PREFIX = "@schema:"
    FIELD_DELIMITER = "|"
    ESCAPE_CHAR = "\\"
    NESTED_SEPARATOR = "."
    ARRAY_SEPARATOR = ","

    def __init__(self, flatten_nested: bool = True, serialize_arrays: bool = True):
        """
        Initialize the TOON converter.

        Args:
            flatten_nested: If True, nested objects are flattened with dot notation.
                           If False, nested objects are serialized as JSON strings.
            serialize_arrays: If True, arrays are serialized as comma-separated values.
                             If False, arrays are serialized as JSON strings.
        """
        self.flatten_nested = flatten_nested
        self.serialize_arrays = serialize_arrays

    def _escape_value(self, value: str) -> str:
        """Escape pipe characters in a value."""
        if value is None:
            return ""
        return str(value).replace(self.FIELD_DELIMITER, self.ESCAPE_CHAR + self.FIELD_DELIMITER)

    def _unescape_value(self, value: str) -> str:
        """Unescape pipe characters in a value."""
        return value.replace(self.ESCAPE_CHAR + self.FIELD_DELIMITER, self.FIELD_DELIMITER)

    def _flatten_object(self, obj: dict, prefix: str = "") -> dict:
        """
        Flatten a nested object using dot notation.

        Args:
            obj: The object to flatten
            prefix: Current key prefix for nested keys

        Returns:
            Flattened dictionary with dot-notation keys
        """
        result = {}
        for key, value in obj.items():
            new_key = f"{prefix}{self.NESTED_SEPARATOR}{key}" if prefix else key

            if isinstance(value, dict) and self.flatten_nested:
                # Recursively flatten nested objects
                result.update(self._flatten_object(value, new_key))
            elif isinstance(value, list) and self.serialize_arrays:
                # Serialize arrays as comma-separated values
                if all(isinstance(item, (str, int, float, bool)) or item is None for item in value):
                    result[new_key] = self.ARRAY_SEPARATOR.join(str(item) if item is not None else "" for item in value)
                else:
                    # Complex arrays - serialize as JSON string
                    import json
                    result[new_key] = json.dumps(value)
            elif isinstance(value, (dict, list)):
                # Serialize complex types as JSON strings
                import json
                result[new_key] = json.dumps(value)
            else:
                result[new_key] = value

        return result

    def _extract_schema(self, objects: list[dict]) -> list[str]:
        """
        Extract a unified schema from all objects.

        Args:
            objects: List of dictionaries to extract schema from

        Returns:
            List of attribute names (schema)
        """
        if not objects:
            return []

        # Collect all unique keys while preserving order from first object
        schema = list(self._flatten_object(objects[0]).keys())
        seen = set(schema)

        # Add any additional keys from other objects
        for obj in objects[1:]:
            flat_obj = self._flatten_object(obj)
            for key in flat_obj.keys():
                if key not in seen:
                    schema.append(key)
                    seen.add(key)

        return schema

    def json_to_toon(self, data: list[dict]) -> str:
        """
        Convert a list of JSON objects to TOON format.

        Args:
            data: List of dictionaries to convert

        Returns:
            TOON formatted string

        Raises:
            TOONConversionError: If conversion fails
        """
        if not isinstance(data, list):
            raise TOONConversionError("Input must be a list of dictionaries")

        if not data:
            return ""

        if not all(isinstance(item, dict) for item in data):
            raise TOONConversionError("All items in the list must be dictionaries")

        try:
            # Extract schema
            schema = self._extract_schema(data)
            schema_line = f"{self.SCHEMA_PREFIX}{self.ARRAY_SEPARATOR.join(schema)}"

            # Convert each object to a data row
            data_rows = []
            for obj in data:
                flat_obj = self._flatten_object(obj)
                values = []
                for attr in schema:
                    value = flat_obj.get(attr)
                    if value is None:
                        values.append("")
                    else:
                        values.append(self._escape_value(str(value)))
                data_rows.append(self.FIELD_DELIMITER.join(values))

            return schema_line + "\n" + "\n".join(data_rows)

        except Exception as e:
            raise TOONConversionError(f"Failed to convert JSON to TOON: {e}")

    def toon_to_json(self, toon_string: str) -> list[dict]:
        """
        Convert a TOON formatted string back to JSON.

        Args:
            toon_string: TOON formatted string

        Returns:
            List of dictionaries

        Raises:
            TOONParseError: If parsing fails
        """
        if not toon_string or not toon_string.strip():
            return []

        try:
            lines = toon_string.strip().split("\n")

            if not lines:
                return []

            # Parse schema line
            schema_line = lines[0]
            if not schema_line.startswith(self.SCHEMA_PREFIX):
                raise TOONParseError(f"First line must start with '{self.SCHEMA_PREFIX}'")

            schema_str = schema_line[len(self.SCHEMA_PREFIX):]
            schema = schema_str.split(self.ARRAY_SEPARATOR)

            # Parse data rows
            result = []
            for line in lines[1:]:
                if not line.strip():
                    continue

                # Split by unescaped pipe delimiter
                values = self._split_escaped(line)

                # Pad with empty strings if fewer values than schema
                while len(values) < len(schema):
                    values.append("")

                # Build object from schema and values
                obj = {}
                for attr, value in zip(schema, values):
                    unescaped_value = self._unescape_value(value)
                    # Handle nested keys (dot notation)
                    self._set_nested_value(obj, attr, unescaped_value)

                result.append(obj)

            return result

        except TOONParseError:
            raise
        except Exception as e:
            raise TOONParseError(f"Failed to parse TOON: {e}")

    def _split_escaped(self, line: str) -> list[str]:
        """Split a line by pipe delimiter, respecting escaped pipes."""
        result = []
        current = []
        i = 0
        while i < len(line):
            if line[i] == self.ESCAPE_CHAR and i + 1 < len(line) and line[i + 1] == self.FIELD_DELIMITER:
                # Escaped pipe - include the escape sequence
                current.append(self.ESCAPE_CHAR + self.FIELD_DELIMITER)
                i += 2
            elif line[i] == self.FIELD_DELIMITER:
                result.append("".join(current))
                current = []
                i += 1
            else:
                current.append(line[i])
                i += 1
        result.append("".join(current))
        return result

    def _set_nested_value(self, obj: dict, key: str, value: str) -> None:
        """Set a value in a nested dictionary using dot notation key."""
        if self.NESTED_SEPARATOR not in key:
            obj[key] = value if value else None
            return

        parts = key.split(self.NESTED_SEPARATOR)
        current = obj
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value if value else None


# Convenience functions for simple usage
_default_converter = TOONConverter()


def json_to_toon(data: list[dict], **kwargs) -> str:
    """
    Convert a list of JSON objects to TOON format.

    Args:
        data: List of dictionaries to convert
        **kwargs: Options passed to TOONConverter

    Returns:
        TOON formatted string

    Example:
        >>> data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        >>> print(json_to_toon(data))
        @schema:name,age
        John|30
        Jane|25
    """
    if kwargs:
        converter = TOONConverter(**kwargs)
        return converter.json_to_toon(data)
    return _default_converter.json_to_toon(data)


def toon_to_json(toon_string: str, **kwargs) -> list[dict]:
    """
    Convert a TOON formatted string back to JSON.

    Args:
        toon_string: TOON formatted string
        **kwargs: Options passed to TOONConverter

    Returns:
        List of dictionaries

    Example:
        >>> toon = "@schema:name,age\\nJohn|30\\nJane|25"
        >>> toon_to_json(toon)
        [{'name': 'John', 'age': '30'}, {'name': 'Jane', 'age': '25'}]
    """
    if kwargs:
        converter = TOONConverter(**kwargs)
        return converter.toon_to_json(toon_string)
    return _default_converter.toon_to_json(toon_string)
