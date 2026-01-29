import pytest
from strpro.utils import extract_and_parse_json


class TestExtractAndParseJson:
    """Test suite for extract_and_parse_json function."""

    def test_single_complete_json_object(self):
        """Test Case 1: Single, complete JSON object."""
        text = "Some text before {\"name\": \"Alice\", \"age\": 30} and after."
        expected = [{"name": "Alice", "age": 30}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_multiple_complete_json_objects(self):
        """Test Case 2: Multiple, complete JSON objects."""
        text = "User 1: {\"id\": 1, \"status\": \"active\"}. User 2: {\"id\": 2, \"status\": \"inactive\"}."
        expected = [{"id": 1, "status": "active"}, {"id": 2, "status": "inactive"}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_no_json_in_string(self):
        """Test Case 3: No JSON in the string."""
        text = "This string has no JSON data at all."
        expected = []
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_array(self):
        """Test Case 4: JSON array."""
        text = "Here's a list: [{\"item\": \"apple\"}, {\"item\": \"banana\"}]."
        expected = [{"item": "apple"}, {"item": "banana"}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_mixed_json_object_and_array(self):
        """Test Case 5: Mixed JSON object and array."""
        text = "Data 1: {\"type\": \"user\"} List: [1, 2, 3] More text."
        expected = [{"type": "user"}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_with_nested_structure(self):
        """Test Case 6: JSON with nested structure."""
        text = "Nested data: {\"outer\": {\"inner\": \"value\"}, \"count\": 10}."
        expected = [{"outer": {"inner": "value"}, "count": 10}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_incomplete_json_skipped(self):
        """Test Case 7: Incomplete JSON (should be skipped)."""
        text = "Invalid data: {\"key\": \"value\", \"incomplete\":"
        expected = []
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_with_escaped_quotes_and_complex_strings(self):
        """Test Case 8: JSON with escaped quotes and complex strings."""
        text = 'Message: {"text": "This is a \\"complex\\" string with \\n newlines.", "code": 200}. End.'
        expected = [{"text": "This is a \"complex\" string with \n newlines.", "code": 200}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_malformed_array_skipped(self):
        """Test Case 9: JSON string that looks like an array but isn't quite valid."""
        text = "Malformed array: [1, 2, 3, "
        expected = []
        result = extract_and_parse_json(text)
        assert result == expected

    def test_multiple_jsons_with_text_between(self):
        """Test Case 10: Multiple JSONs with other text in between."""
        text = "Log: {\"level\": \"info\"} Intermediary text. Error: {\"code\": 500, \"message\": \"Failed\"}"
        expected = [{"level": "info"}, {"code": 500, "message": "Failed"}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_empty_json_object_and_array(self):
        """Test Case 11: Empty JSON object and array."""
        text = "Empty obj: {} Empty array: []"
        expected = [{}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_mismatched_braces_brackets_skipped(self):
        """Test Case 12: JSON with mismatched braces/brackets (should be skipped)."""
        text = "Mismatched: {\"key\": \"value\"]"
        expected = []
        result = extract_and_parse_json(text)
        assert result == expected

    def test_just_braces_valid_empty_jsons(self):
        """Test Case 13: Text containing just braces/brackets, which are valid empty JSONs."""
        text = "Just braces {}{}"
        expected = [{}, {}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_nested_within_array(self):
        """Test Case 14: JSON nested within an array."""
        text = "Outer array: [1, {\"nested\": \"json\"}, 3]"
        expected = [{"nested": "json"}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_with_braces_in_string_value(self):
        """Test Case 15: JSON with braces in string value."""
        text = '''log: {"msg": "this looks like { not json }", "ok": true}'''
        expected = [{"msg": "this looks like { not json }", "ok": True}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_with_pattern_in_string(self):
        """Test Case 16: JSON with pattern in string value."""
        text = '''data: {"pattern": "[a-z]+", "valid": true}'''
        expected = [{"pattern": "[a-z]+", "valid": True}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_with_escaped_quotes_in_string(self):
        """Test Case 17: JSON with escaped quotes in string value."""
        text = r'''response: {"text": "She said: \"{hello}\"", "id": 1}'''
        expected = [{"text": "She said: \"{hello}\"", "id": 1}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_multiple_jsons_with_noise(self):
        """Test Case 18: Multiple JSONs with noise around them."""
        text = '''{"a": 1}{"b": 2}     Noise }}} start {"x": 1, "y": 2} end {{{ noise'''
        expected = [{"a": 1}, {"b": 2}, {"x": 1, "y": 2}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_json_in_markdown_code_block(self):
        """Test Case 19: JSON in markdown code block."""
        text = '''Here is the payload:
    ```json
    {"a": 1, "b": 2}       
    '''
        expected = [{"a": 1, "b": 2}]
        result = extract_and_parse_json(text)
        assert result == expected

    def test_complex_drowning_test_data(self):
        """Test with complex drowning test insights data."""
        s = "{\n  \"insights\": [\n    {\n      \"section\": \"domain_concepts\",\n      \"text\": \"The Gettler test measures chloride concentration in blood to confirm drowning.\"\n    },\n    {\n      \"section\": \"domain_concepts\",\n      \"text\": \"Diatoms in water are used to confirm drowning.\"\n    },\n    {\n      \"section\": \"pitfalls\",\n      \"text\": \"When a forensic test question asks what the test detects, focus on the test's primary measurement; distractors often involve unrelated parameters such as lung weight or magnesium content.\"\n    },\n    {\n      \"section\": \"mechanisms\",\n      \"text\": \"In drowning, chloride concentration in blood rises due to water ingestion, which is detected by the Gettler test.\"\n    }\n  ]\n}"
        result = extract_and_parse_json(s)
        assert len(result) == 1
        assert "insights" in result[0]
        assert len(result[0]["insights"]) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
