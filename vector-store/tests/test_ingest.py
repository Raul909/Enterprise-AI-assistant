
import sys
import os
import pytest

# Add vector-store directory to path to import ingest
# Current file: vector-store/tests/test_ingest.py
# Parent: vector-store/tests
# Grandparent: vector-store
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingest import chunk_text

class TestChunkText:
    def test_basic_chunking(self):
        """Test basic chunking functionality with overlap."""
        text = "one two three four five six seven eight nine ten"
        # chunk_size=5, overlap=2
        # 1: one two three four five (0-5)
        # next start: 5 - 2 = 3
        # 2: four five six seven eight (3-8)
        # next start: 8 - 2 = 6
        # 3: seven eight nine ten (6-10) -> length 4, loop ends?

        chunks = chunk_text(text, chunk_size=5, overlap=2)

        expected = [
            "one two three four five",
            "four five six seven eight",
            "seven eight nine ten",
            "ten"
        ]
        assert chunks == expected

    def test_short_text(self):
        """Test text shorter than chunk size."""
        text = "short text"
        chunks = chunk_text(text, chunk_size=5, overlap=1)
        assert len(chunks) == 1
        assert chunks[0] == "short text"

    def test_exact_size(self):
        """Test text exactly the chunk size."""
        text = "one two three"
        chunks = chunk_text(text, chunk_size=3, overlap=1)
        assert len(chunks) == 1
        assert chunks[0] == "one two three"

    def test_empty_string(self):
        """Test empty string input."""
        text = ""
        chunks = chunk_text(text, chunk_size=5, overlap=1)
        assert chunks == [""]

    def test_no_overlap(self):
        """Test chunking with zero overlap."""
        text = "one two three four five six"
        chunks = chunk_text(text, chunk_size=3, overlap=0)
        expected = [
            "one two three",
            "four five six"
        ]
        assert chunks == expected

    def test_custom_parameters(self):
        """Test with non-default parameters."""
        text = "a b c d e f"
        chunks = chunk_text(text, chunk_size=2, overlap=1)
        # 1. a b (start 0, end 2) -> next 1
        # 2. b c (start 1, end 3) -> next 2
        # 3. c d (start 2, end 4) -> next 3
        # 4. d e (start 3, end 5) -> next 4
        # 5. e f (start 4, end 6) -> next 5
        # 6. f (start 5, end 7) -> next 6
        assert len(chunks) == 6
        assert chunks[0] == "a b"
        assert chunks[1] == "b c"
        assert chunks[-1] == "f"

    def test_invalid_parameters(self):
        """Test that invalid parameters raise ValueError."""
        text = "some text"

        # Overlap equal to chunk size (would cause infinite loop)
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            chunk_text(text, chunk_size=5, overlap=5)

        # Overlap greater than chunk size (would cause infinite loop / negative progress)
        with pytest.raises(ValueError, match="overlap must be less than chunk_size"):
            chunk_text(text, chunk_size=5, overlap=6)

        # Negative overlap
        with pytest.raises(ValueError, match="overlap must be non-negative"):
            chunk_text(text, chunk_size=5, overlap=-1)

        # Zero chunk size
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_text(text, chunk_size=0, overlap=0)

        # Negative chunk size
        with pytest.raises(ValueError, match="chunk_size must be positive"):
            chunk_text(text, chunk_size=-5, overlap=0)
