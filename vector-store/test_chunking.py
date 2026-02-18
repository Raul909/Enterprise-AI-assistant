import sys
from unittest.mock import MagicMock

# Mock dependencies that are not available
sys.modules["faiss"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

import pytest
from ingest import chunk_text

def test_chunk_text_basic():
    """Test basic chunking with overlap."""
    text = "one two three four five six seven eight nine ten"
    # chunk_size=5, overlap=2
    chunks = chunk_text(text, chunk_size=5, overlap=2)

    # Chunk 1: words[0:5] -> "one two three four five"
    # Chunk 2: start = 5-2 = 3. words[3:8] -> "four five six seven eight"
    # Chunk 3: start = 8-2 = 6. words[6:11] -> "seven eight nine ten"
    # Chunk 4: start = 11-2 = 9. words[9:14] -> "ten"

    assert chunks == [
        "one two three four five",
        "four five six seven eight",
        "seven eight nine ten",
        "ten"
    ]

def test_chunk_text_empty():
    """Test chunking an empty string."""
    assert chunk_text("", chunk_size=5, overlap=2) == [""]

def test_chunk_text_short():
    """Test chunking text shorter than chunk_size."""
    text = "one two three"
    assert chunk_text(text, chunk_size=5, overlap=2) == [text]

def test_chunk_text_exact():
    """Test chunking text exactly chunk_size."""
    text = "one two three four five"
    assert chunk_text(text, chunk_size=5, overlap=2) == [text]

def test_chunk_text_no_overlap():
    """Test chunking with zero overlap."""
    text = "one two three four five six"
    chunks = chunk_text(text, chunk_size=3, overlap=0)
    assert chunks == ["one two three", "four five six"]

def test_chunk_text_whitespace():
    """Test chunking with irregular whitespace."""
    text = "one  two\nthree\tfour  five"
    chunks = chunk_text(text, chunk_size=2, overlap=0)
    # .split() without arguments splits by any whitespace and discards empty strings
    assert chunks == ["one two", "three four", "five"]

def test_chunk_text_single_word_chunks():
    """Test chunking with chunk_size of 1."""
    text = "one two three"
    chunks = chunk_text(text, chunk_size=1, overlap=0)
    assert chunks == ["one", "two", "three"]

def test_chunk_text_overlap_edge_case():
    """Test chunking where overlap >= chunk_size. Should raise ValueError."""
    text = "one two three four five"
    with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
        chunk_text(text, chunk_size=3, overlap=3)

def test_chunk_text_invalid_size():
    """Test chunking with invalid chunk_size."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        chunk_text("hello", chunk_size=0)
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        chunk_text("hello", chunk_size=-1)

def test_chunk_text_invalid_overlap():
    """Test chunking with negative overlap."""
    with pytest.raises(ValueError, match="overlap must be non-negative"):
        chunk_text("hello", chunk_size=5, overlap=-1)
