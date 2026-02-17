import sys
import os
from unittest.mock import MagicMock

# Calculate paths
# Current file is in backend/tests/
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
app_dir = os.path.join(backend_dir, "app")

# Add backend/app to sys.path so imports like 'core.config' work
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Also add backend to sys.path just in case
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

# Mock sentence_transformers since it's not installed in the test environment
sys.modules["sentence_transformers"] = MagicMock()
sys.modules["sentence_transformers.SentenceTransformer"] = MagicMock()

# We might also need to mock anthropic if it wasn't installed, but it is.
# Check other imports in ai_orchestrator.py
# from openai import OpenAI -> openai is installed
# import anthropic -> anthropic is installed
