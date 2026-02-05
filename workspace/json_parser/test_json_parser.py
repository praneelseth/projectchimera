import json as stdlib_json
import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import the student's implementation
from json_parser import parse_json


class TestJSONParserBasics:
    """Test basic JSON data types."""
    
    def test_null(self):
        assert parse_json('null') is None
    
    def test_true(self):
        assert parse_json('true') is True
    
    def test_false(self):
        assert parse_json('false') is False
    
    def test_integer(self):
        assert parse_json('42') == 42
        assert parse_json('-42') == -42
        assert parse_json('0') == 0
    
    def test_float(self):
        assert parse_json('3.14') == 3.14
        assert parse_json('-3.14') == -3.14
        assert parse_json('0.0') == 0.0
    
    def test_scientific_notation(self):
        assert parse_json('1e10') == 1e10
        assert parse_json('1.5e-3') == 0.0015
        assert parse_json('2E+5') == 2e5


class TestJSONParserStrings:
    """Test JSON string parsing."""
    
    def test_simple_string(self):
        assert parse_json('"hello"') == "hello"
        assert parse_json('""') == ""
    
    def test_escape_quote(self):
        assert parse_json('"hello\\"world"') == 'hello"world'
    
    def test_escape_backslash(self):
        assert parse_json('"path\\\\to\\\\file"') == "path\\to\\file"
    
    def test_escape_newline(self):
        assert parse_json('"line1\\nline2"') == "line1\nline2"
    
    def test_escape_tab(self):
        assert parse_json('"col1\\tcol2"') == "col1\tcol2"
    
    def test_escape_sequences(self):
        assert parse_json('"\\r\\n\\b\\f"') == "\r\n\b\f"
    
    def test_unicode_escape(self):
        assert parse_json('"\\u0041"') == "A"
        assert parse_json('"\\u03B1"') == "α"
        assert parse_json('"hello\\u0020world"') == "hello world"
    
    def test_string_with_spaces(self):
        assert parse_json('"hello world"') == "hello world"
    
    def test_string_with_special_chars(self):
        assert parse_json('"!@#$%^&*()"') == "!@#$%^&*()"


class TestJSONParserArrays:
    """Test JSON array parsing."""
    
    def test_empty_array(self):
        assert parse_json('[]') == []
    
    def test_array_of_numbers(self):
        assert parse_json('[1, 2, 3]') == [1, 2, 3]
    
    def test_array_of_strings(self):
        assert parse_json('["a", "b", "c"]') == ["a", "b", "c"]
    
    def test_array_of_mixed_types(self):
        assert parse_json('[1, "hello", true, null]') == [1, "hello", True, None]
    
    def test_nested_arrays(self):
        assert parse_json('[[1, 2], [3, 4]]') == [[1, 2], [3, 4]]
    
    def test_array_with_whitespace(self):
        assert parse_json('[ 1 , 2 , 3 ]') == [1, 2, 3]


class TestJSONParserObjects:
    """Test JSON object parsing."""
    
    def test_empty_object(self):
        assert parse_json('{}') == {}
    
    def test_simple_object(self):
        assert parse_json('{"key": "value"}') == {"key": "value"}
    
    def test_object_with_multiple_keys(self):
        assert parse_json('{"a": 1, "b": 2}') == {"a": 1, "b": 2}
    
    def test_object_mixed_types(self):
        result = parse_json('{"name": "Alice", "age": 30, "active": true}')
        assert result == {"name": "Alice", "age": 30, "active": True}
    
    def test_nested_objects(self):
        result = parse_json('{"user": {"name": "Alice"}}')
        assert result == {"user": {"name": "Alice"}}
    
    def test_object_with_whitespace(self):
        result = parse_json('{ "key" : "value" }')
        assert result == {"key": "value"}
    
    def test_object_with_array(self):
        result = parse_json('{"items": [1, 2, 3]}')
        assert result == {"items": [1, 2, 3]}


class TestJSONParserComplex:
    """Test complex nested structures."""
    
    def test_array_of_objects(self):
        result = parse_json('[{"id": 1}, {"id": 2}]')
        assert result == [{"id": 1}, {"id": 2}]
    
    def test_deeply_nested(self):
        result = parse_json('{"a": {"b": {"c": [1, 2, 3]}}}')
        assert result == {"a": {"b": {"c": [1, 2, 3]}}}
    
    def test_real_world_json(self):
        json_str = '{"user": {"name": "Alice", "age": 30}, "scores": [85, 90, 92], "active": true}'
        result = parse_json(json_str)
        assert result == {
            "user": {"name": "Alice", "age": 30},
            "scores": [85, 90, 92],
            "active": True
        }
    
    def test_large_structure(self):
        json_str = '''
        {
            "items": [
                {"id": 1, "name": "item1", "tags": ["a", "b"]},
                {"id": 2, "name": "item2", "tags": ["c", "d"]}
            ],
            "count": 2,
            "active": true
        }
        '''
        result = parse_json(json_str)
        assert len(result["items"]) == 2
        assert result["count"] == 2


class TestJSONParserErrors:
    """Test error handling."""
    
    def test_unclosed_brace(self):
        with pytest.raises(ValueError):
            parse_json('{')
    
    def test_unclosed_bracket(self):
        with pytest.raises(ValueError):
            parse_json('[')
    
    def test_unexpected_character(self):
        with pytest.raises(ValueError):
            parse_json('{invalid}')
    
    def test_trailing_comma_in_array(self):
        with pytest.raises(ValueError):
            parse_json('[1, 2,]')
    
    def test_trailing_comma_in_object(self):
        with pytest.raises(ValueError):
            parse_json('{"key": "value",}')
    
    def test_single_quotes(self):
        with pytest.raises(ValueError):
            parse_json("{'key': 'value'}")
    
    def test_unquoted_key(self):
        with pytest.raises(ValueError):
            parse_json('{key: "value"}')
    
    def test_missing_colon(self):
        with pytest.raises(ValueError):
            parse_json('{"key" "value"}')
    
    def test_undefined_value(self):
        with pytest.raises(ValueError):
            parse_json('{"key": undefined}')
    
    def test_invalid_escape(self):
        with pytest.raises(ValueError):
            parse_json('"\\x"')


class TestJSONParserEdgeCases:
    """Test edge cases."""
    
    def test_empty_string(self):
        assert parse_json('""') == ""
    
    def test_whitespace_only_string(self):
        assert parse_json('"   "') == "   "
    
    def test_number_zero(self):
        assert parse_json('0') == 0
    
    def test_negative_zero(self):
        assert parse_json('-0') == 0
    
    def test_large_number(self):
        assert parse_json('999999999999999') == 999999999999999
    
    def test_leading_zeros_invalid(self):
        # JSON doesn't allow leading zeros (except for 0 itself)
        with pytest.raises(ValueError):
            parse_json('01')
    
    def test_leading_whitespace(self):
        assert parse_json('   [1, 2, 3]') == [1, 2, 3]
    
    def test_trailing_whitespace(self):
        assert parse_json('[1, 2, 3]   ') == [1, 2, 3]
    
    def test_extra_content_after_json(self):
        # Extra content after valid JSON should be an error
        with pytest.raises(ValueError):
            parse_json('[1, 2, 3] extra')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
