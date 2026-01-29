# API Reference

## strpro.utils

### `extract_and_parse_json(text: str) -> list[dict]`

Extracts JSON objects (dictionaries) from arbitrary text.

**Parameters:**
- `text` (str): The input text containing JSON objects

**Returns:**
- `list[dict]`: A list of dictionaries extracted from the text

**Behavior:**
- Only dictionaries are returned in the results
- Arrays within the text are traversed to extract dictionaries inside them
- Non-JSON content is ignored
- Invalid JSON is skipped without raising an error
- Partial/incomplete JSON is ignored

**Examples:**

```python
from strpro.utils import extract_and_parse_json

# Single JSON object
text1 = "User info: {\"name\": \"Alice\", \"age\": 30}"
result1 = extract_and_parse_json(text1)
# Output: [{"name": "Alice", "age": 30}]

# Multiple JSON objects
text2 = "{\"id\": 1} and {\"id\": 2}"
result2 = extract_and_parse_json(text2)
# Output: [{"id": 1}, {"id": 2}]

# JSON array (extracts dicts inside)
text3 = "Data: [{\"item\": \"apple\"}, {\"item\": \"banana\"}]"
result3 = extract_and_parse_json(text3)
# Output: [{"item": "apple"}, {"item": "banana"}]

# Complex nested structure
text4 = "Config: {\"outer\": {\"inner\": \"value\"}, \"count\": 10}"
result4 = extract_and_parse_json(text4)
# Output: [{"outer": {"inner": "value"}, "count": 10}]
```

**Error Handling:**
- Incomplete JSON is silently ignored
- Malformed JSON does not raise exceptions
- If no valid JSON is found, an empty list is returned
