import re
import json
from typing import Any, List
def extract_and_parse_json(text: str) -> list[dict]:
    """
    Extracts JSON objects (dict) from arbitrary text.
    - Only dicts are returned
    - Arrays are traversed to extract dicts inside
    - Non-JSON content is ignored
    """
    decoder = json.JSONDecoder()
    results: List[dict] = []

    def collect_objects(obj: Any):
        if isinstance(obj, dict):
            results.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                collect_objects(item)

    i = 0
    n = len(text)

    while i < n:
        if text[i] in '{[':
            try:
                parsed, end = decoder.raw_decode(text[i:])
                collect_objects(parsed)
                i += end
                continue
            except json.JSONDecodeError:
                pass
        i += 1

    return results


