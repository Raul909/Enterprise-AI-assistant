
import pytest
from ingest import chunk_text, CHUNK_SIZE, CHUNK_OVERLAP

# Since vector_store is not a package, we might need to adjust imports
# Depending on how pytest is run, we might need sys.path hack or proper structure
# But let's assume standard pytest discovery works if run from root with python -m pytest
# or by adding conftest.py or setting PYTHONPATH.

def test_chunk_text_basic():
    """Test basic chunking functionality with default parameters."""
    text = "word " * (CHUNK_SIZE + 10)
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(isinstance(c, str) for c in chunks)

def test_chunk_text_small_text():
    """Test chunking when text is smaller than chunk size."""
    text = "This is a small text."
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_text_exact_size():
    """Test chunking when text is exactly the chunk size."""
    words = ["word"] * 10
    text = " ".join(words)
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0] == text

def test_chunk_text_overlap():
    """Test that chunks overlap correctly."""
    # Create a sequence of unique words to easily verify overlap
    words = [str(i) for i in range(20)]
    text = " ".join(words)
    chunk_size = 10
    overlap = 2

    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    # Expected behavior:
    # Chunk 1: 0-9 (10 words)
    # Next start: 10 - 2 = 8
    # Chunk 2: 8-17 (10 words)
    # Next start: 18 - 2 = 16
    # Chunk 3: 16-19 (4 words)

    assert len(chunks) == 3

    c1_words = chunks[0].split()
    c2_words = chunks[1].split()
    c3_words = chunks[2].split()

    assert len(c1_words) == 10
    assert c1_words[-2:] == c2_words[:2]  # Check overlap between c1 and c2
    assert c2_words[-2:] == c3_words[:2]  # Check overlap between c2 and c3

    assert c1_words[0] == "0"
    assert c1_words[-1] == "9"
    assert c2_words[0] == "8"
    assert c2_words[-1] == "17"
    assert c3_words[0] == "16"
    assert c3_words[-1] == "19"

def test_chunk_text_empty():
    """Test chunking with empty string."""
    text = ""
    chunks = chunk_text(text)
    # Current implementation returns [""] for empty string because [""] has length 1 <= chunk_size
    # Or strict empty string check.
    # text.split() returns [] for empty string.
    # len([]) is 0. 0 <= chunk_size. Returns [text] which is [""]
    assert chunks == [""]

def test_chunk_text_single_word():
    """Test chunking with a single word."""
    text = "word"
    chunks = chunk_text(text, chunk_size=10, overlap=2)
    assert len(chunks) == 1
    assert chunks[0] == "word"

def test_chunk_text_custom_params():
    """Test with custom chunk size and overlap."""
    text = "one two three four five six"
    chunks = chunk_text(text, chunk_size=3, overlap=1)
    # words: one, two, three, four, five, six
    # 1: one two three (start=0, end=3) -> next start = 3-1=2
    # 2: three four five (start=2, end=5) -> next start = 5-1=4
    # 3: five six (start=4, end=7) -> next start = 7-1=6

    assert len(chunks) == 3
    assert chunks[0] == "one two three"
    assert chunks[1] == "three four five"
    assert chunks[2] == "five six"

def test_chunk_text_invalid_inputs():
    """Test that invalid inputs raise ValueError."""
    text = "some text"

    # Chunk size <= 0
    with pytest.raises(ValueError):
        chunk_text(text, chunk_size=0)

    with pytest.raises(ValueError):
        chunk_text(text, chunk_size=-1)

    # Overlap < 0
    with pytest.raises(ValueError):
        chunk_text(text, overlap=-1)

    # Overlap >= chunk_size
    with pytest.raises(ValueError):
        chunk_text(text, chunk_size=10, overlap=10)

    with pytest.raises(ValueError):
        chunk_text(text, chunk_size=10, overlap=11)
