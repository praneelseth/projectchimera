# JSON Parser Implementation Task

## Objective
Implement a complete, working JSON parser from scratch without external libraries.

## Requirements

### Core Functionality
Parse all JSON data types:
- **Strings**: With escape sequences (\", \\, \n, \t, \r, \b, \f, \uXXXX)
- **Numbers**: Integers, floats, negative, scientific notation (1e10, 1.5e-3)
- **Booleans**: `true` and `false`
- **Null**: `null`
- **Arrays**: Ordered collections `[1, 2, 3]`
- **Objects**: Key-value pairs `{"key": "value"}`
- **Nested structures**: Objects within arrays, arrays within objects

### Input/Output Contract
```python
def parse_json(text: str) -> any:
    """
    Parse a JSON string and return equivalent Python object.
    
    Args:
        text: Valid JSON string
    
    Returns:
        Python object (dict, list, str, int, float, bool, None)
    
    Raises:
        ValueError: If JSON is invalid with descriptive message
    """
```

### Error Handling
Raise `ValueError` with clear messages for:
- Invalid syntax
- Unexpected characters
- Unclosed brackets/braces
- Invalid escape sequences
- Trailing commas
- Duplicate keys (optional warning)
- Numbers in invalid format

### Constraints
- **No external libraries**: Implement JSON parsing from scratch
- **No regex**: Use character-by-character parsing
- **Code length**: Maximum 300 lines
- **Performance**: Parse 1MB JSON in < 1 second

## Test Cases

The implementation must pass these cases:

```python
# Simple types
parse_json('null') == None
parse_json('true') == True
parse_json('false') == False
parse_json('42') == 42
parse_json('3.14') == 3.14
parse_json('"hello"') == "hello"

# Escape sequences
parse_json('"hello\\"world"') == 'hello"world'
parse_json('"line1\\nline2"') == "line1\nline2"
parse_json('"tab\\there"') == "tab\there"

# Collections
parse_json('[1, 2, 3]') == [1, 2, 3]
parse_json('[]') == []
parse_json('{"name": "Alice"}') == {"name": "Alice"}
parse_json('{}') == {}

# Nested structures
parse_json('[{"id": 1}, {"id": 2}]') == [{"id": 1}, {"id": 2}]
parse_json('{"items": [1, 2], "count": 2}') == {"items": [1, 2], "count": 2}

# Edge cases
parse_json('-42') == -42
parse_json('1e10') == 1e10
parse_json('1.5e-3') == 1.5e-3
parse_json('"\\u0041"') == "A"

# Real-world example
parse_json('{"name":"Alice","age":30,"active":true,"scores":[85,90,92]}') == {
    "name": "Alice",
    "age": 30,
    "active": True,
    "scores": [85, 90, 92]
}

# Invalid JSON (should raise ValueError)
parse_json('{')  # Unclosed
parse_json('{"key": undefined}')  # Invalid value
parse_json('[1, 2,]')  # Trailing comma (strict mode)
parse_json("{'key': 'value'}")  # Single quotes not allowed
```

## Success Criteria

- [ ] All 20+ unit tests pass
- [ ] Parser correctly handles all data types
- [ ] Parser has proper error handling
- [ ] Code is under 300 lines
- [ ] Code is well-documented
- [ ] Parser performance is acceptable

## Implementation Hints

1. **Tokenization**: Identify JSON tokens (strings, numbers, literals, delimiters)
2. **Parsing**: Build recursive descent parser
3. **String Handling**: Carefully handle escape sequences
4. **Number Parsing**: Support int, float, scientific notation
5. **Recursion**: Use recursion for nested structures

## File Structure
```
workspace/json_parser/
├── spec.md              (this file)
├── plan.md              (agent creates)
├── test_json_parser.py  (provided)
└── src/
    └── json_parser.py   (agent creates)
```
