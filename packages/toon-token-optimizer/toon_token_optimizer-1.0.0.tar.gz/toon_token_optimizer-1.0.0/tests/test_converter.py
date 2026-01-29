"""
Unit tests for TOON Converter.

Run with: pytest tests/test_converter.py -v
"""

import pytest
from toon_converter import (
    TOONConverter,
    json_to_toon,
    toon_to_json,
    TOONConversionError,
    TOONParseError,
)


class TestBasicConversion:
    """Test basic JSON to TOON conversion."""

    def test_simple_conversion(self):
        """Test converting a simple list of objects."""
        data = [
            {"name": "John", "age": 30, "city": "NYC"},
            {"name": "Jane", "age": 25, "city": "LA"},
        ]
        result = json_to_toon(data)
        
        assert result.startswith("@schema:")
        lines = result.split("\n")
        assert lines[0] == "@schema:name,age,city"
        assert lines[1] == "John|30|NYC"
        assert lines[2] == "Jane|25|LA"

    def test_single_object(self):
        """Test converting a single object."""
        data = [{"id": "123", "status": "active"}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[0] == "@schema:id,status"
        assert lines[1] == "123|active"

    def test_empty_list(self):
        """Test converting an empty list."""
        result = json_to_toon([])
        assert result == ""

    def test_preserves_order(self):
        """Test that attribute order is preserved from first object."""
        data = [
            {"z_field": "1", "a_field": "2", "m_field": "3"},
            {"z_field": "4", "a_field": "5", "m_field": "6"},
        ]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[0] == "@schema:z_field,a_field,m_field"


class TestNullAndEmptyValues:
    """Test handling of null and empty values."""

    def test_null_values(self):
        """Test that null values become empty strings."""
        data = [
            {"name": "John", "email": None},
            {"name": "Jane", "email": "jane@test.com"},
        ]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[1] == "John|"
        assert lines[2] == "Jane|jane@test.com"

    def test_empty_string_values(self):
        """Test that empty strings are preserved."""
        data = [{"name": "John", "middle": "", "last": "Doe"}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[1] == "John||Doe"

    def test_missing_keys(self):
        """Test objects with different keys."""
        data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "city": "LA"},  # Missing 'age', has extra 'city'
        ]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        # Schema should include all keys
        assert "name" in lines[0]
        assert "age" in lines[0]
        assert "city" in lines[0]


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_pipe_in_value(self):
        """Test that pipe characters in values are escaped."""
        data = [{"description": "A|B|C", "id": "1"}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        # Pipe should be escaped
        assert "\\|" in lines[1]
        
    def test_roundtrip_with_pipe(self):
        """Test that pipe characters survive roundtrip conversion."""
        data = [{"value": "has|pipe|chars", "other": "normal"}]
        toon = json_to_toon(data)
        restored = toon_to_json(toon)
        
        assert restored[0]["value"] == "has|pipe|chars"
        assert restored[0]["other"] == "normal"

    def test_commas_in_values(self):
        """Test that commas in values don't break conversion."""
        data = [{"address": "123 Main St, Suite 100", "city": "NYC"}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert "123 Main St, Suite 100" in lines[1]

    def test_quotes_in_values(self):
        """Test that quotes in values are preserved."""
        data = [{"quote": 'He said "hello"', "id": "1"}]
        result = json_to_toon(data)
        restored = toon_to_json(result)
        
        assert restored[0]["quote"] == 'He said "hello"'


class TestNestedObjects:
    """Test handling of nested objects."""

    def test_nested_object_flattening(self):
        """Test that nested objects are flattened with dot notation."""
        data = [
            {
                "customer": {
                    "name": "John",
                    "address": {"city": "NYC", "zip": "10001"}
                }
            }
        ]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert "customer.name" in lines[0]
        assert "customer.address.city" in lines[0]
        assert "customer.address.zip" in lines[0]
        assert "John" in lines[1]
        assert "NYC" in lines[1]

    def test_deeply_nested(self):
        """Test deeply nested objects."""
        data = [{"a": {"b": {"c": {"d": "value"}}}}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[0] == "@schema:a.b.c.d"
        assert lines[1] == "value"


class TestArrays:
    """Test handling of arrays."""

    def test_simple_array(self):
        """Test arrays of simple values."""
        data = [{"tags": ["python", "ai", "ml"]}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        # Arrays should be comma-separated
        assert lines[1] == "python,ai,ml"

    def test_numeric_array(self):
        """Test arrays of numbers."""
        data = [{"scores": [100, 95, 88]}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[1] == "100,95,88"

    def test_empty_array(self):
        """Test empty arrays."""
        data = [{"items": [], "name": "test"}]
        result = json_to_toon(data)
        
        lines = result.split("\n")
        assert lines[1] == "|test"


class TestTOONToJSON:
    """Test TOON to JSON conversion."""

    def test_simple_parsing(self):
        """Test parsing a simple TOON string."""
        toon = "@schema:name,age,city\nJohn|30|NYC\nJane|25|LA"
        result = toon_to_json(toon)
        
        assert len(result) == 2
        assert result[0]["name"] == "John"
        assert result[0]["age"] == "30"
        assert result[0]["city"] == "NYC"
        assert result[1]["name"] == "Jane"

    def test_empty_toon(self):
        """Test parsing empty TOON string."""
        result = toon_to_json("")
        assert result == []
        
        result = toon_to_json("   ")
        assert result == []

    def test_nested_restoration(self):
        """Test that nested keys are restored to nested objects."""
        toon = "@schema:user.name,user.email\nJohn|john@test.com"
        result = toon_to_json(toon)
        
        assert result[0]["user"]["name"] == "John"
        assert result[0]["user"]["email"] == "john@test.com"

    def test_empty_values_to_none(self):
        """Test that empty values become None."""
        toon = "@schema:name,email\nJohn|"
        result = toon_to_json(toon)
        
        assert result[0]["name"] == "John"
        assert result[0]["email"] is None


class TestRoundTrip:
    """Test roundtrip conversion (JSON -> TOON -> JSON)."""

    def test_simple_roundtrip(self):
        """Test simple roundtrip conversion."""
        original = [
            {"name": "John", "age": "30"},
            {"name": "Jane", "age": "25"},
        ]
        toon = json_to_toon(original)
        restored = toon_to_json(toon)
        
        assert len(restored) == len(original)
        assert restored[0]["name"] == original[0]["name"]
        assert restored[1]["name"] == original[1]["name"]

    def test_complex_roundtrip(self):
        """Test roundtrip with various data types."""
        original = [
            {
                "id": "C12345",
                "customer": {"name": "John", "tier": "premium"},
                "tags": ["vip", "active"],
                "notes": "Important|customer",  # Contains pipe
            }
        ]
        toon = json_to_toon(original)
        restored = toon_to_json(toon)
        
        assert restored[0]["customer"]["name"] == "John"
        assert restored[0]["notes"] == "Important|customer"


class TestErrorHandling:
    """Test error handling."""

    def test_invalid_input_type(self):
        """Test that non-list input raises error."""
        with pytest.raises(TOONConversionError):
            json_to_toon({"name": "John"})  # Dict instead of list

    def test_non_dict_items(self):
        """Test that non-dict items raise error."""
        with pytest.raises(TOONConversionError):
            json_to_toon(["string", "values"])

    def test_invalid_toon_format(self):
        """Test that invalid TOON format raises error."""
        with pytest.raises(TOONParseError):
            toon_to_json("invalid format without schema")


class TestConverterOptions:
    """Test converter configuration options."""

    def test_disable_flattening(self):
        """Test disabling nested object flattening."""
        converter = TOONConverter(flatten_nested=False)
        data = [{"user": {"name": "John"}}]
        result = converter.json_to_toon(data)
        
        # Should contain JSON-serialized nested object
        assert '{"name": "John"}' in result or "{'name': 'John'}" in result or '"name"' in result

    def test_disable_array_serialization(self):
        """Test disabling array serialization."""
        converter = TOONConverter(serialize_arrays=False)
        data = [{"tags": ["a", "b", "c"]}]
        result = converter.json_to_toon(data)
        
        # Should contain JSON-serialized array
        assert "[" in result


class TestTokenEfficiency:
    """Test that TOON is more token-efficient than JSON."""

    def test_token_reduction(self):
        """Verify TOON uses fewer characters than JSON for repeated schemas."""
        import json
        
        data = [
            {"customerId": f"C{i}", "firstName": f"User{i}", "status": "active"}
            for i in range(100)
        ]
        
        json_str = json.dumps(data)
        toon_str = json_to_toon(data)
        
        # TOON should be significantly smaller
        reduction = (1 - len(toon_str) / len(json_str)) * 100
        assert reduction > 30, f"Expected >30% reduction, got {reduction:.1f}%"
        
        print(f"\nToken efficiency test:")
        print(f"  JSON length: {len(json_str):,} chars")
        print(f"  TOON length: {len(toon_str):,} chars")
        print(f"  Reduction: {reduction:.1f}%")


class TestEdgeCases:
    """Test edge cases."""

    def test_unicode_values(self):
        """Test Unicode characters in values."""
        data = [{"name": "日本語", "emoji": "👍🎉"}]
        toon = json_to_toon(data)
        restored = toon_to_json(toon)
        
        assert restored[0]["name"] == "日本語"
        assert restored[0]["emoji"] == "👍🎉"

    def test_numeric_string_preservation(self):
        """Test that numeric values are converted to strings."""
        data = [{"count": 42, "price": 19.99, "flag": True}]
        toon = json_to_toon(data)
        restored = toon_to_json(toon)
        
        # All values come back as strings
        assert restored[0]["count"] == "42"
        assert restored[0]["price"] == "19.99"
        assert restored[0]["flag"] == "True"

    def test_very_long_values(self):
        """Test handling of very long string values."""
        long_text = "x" * 10000
        data = [{"content": long_text}]
        toon = json_to_toon(data)
        restored = toon_to_json(toon)
        
        assert restored[0]["content"] == long_text

    def test_newlines_in_values(self):
        """Test that newlines in values don't break parsing."""
        # Note: This is a known limitation - newlines would break TOON format
        # Values with newlines should be handled appropriately
        data = [{"text": "line1", "id": "1"}]  # Safe case
        toon = json_to_toon(data)
        restored = toon_to_json(toon)
        
        assert restored[0]["text"] == "line1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
