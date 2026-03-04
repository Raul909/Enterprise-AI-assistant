import os
import json

def parse_cors_origins(cors_origins_str):
    try:
        return json.loads(cors_origins_str)
    except (json.JSONDecodeError, TypeError):
        return ["http://localhost:3000", "http://localhost:8000"]

def test_parse_cors_origins():
    # Test with valid JSON list
    assert parse_cors_origins('["http://example.com"]') == ["http://example.com"]

    # Test with multiple origins
    assert parse_cors_origins('["http://a.com", "http://b.com"]') == ["http://a.com", "http://b.com"]

    # Test with invalid JSON (fallback to default)
    assert parse_cors_origins("invalid-json") == ["http://localhost:3000", "http://localhost:8000"]

    # Test with None (fallback to default)
    assert parse_cors_origins(None) == ["http://localhost:3000", "http://localhost:8000"]

    print("All CORS parsing tests passed!")

if __name__ == "__main__":
    test_parse_cors_origins()
