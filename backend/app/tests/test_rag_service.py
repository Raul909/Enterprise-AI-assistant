import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import numpy as np
from services import rag_service as rag_service_module
from services.rag_service import rag_service
from models.document import Document

@pytest.mark.asyncio
async def test_semantic_search():
    # Mock FAISS index
    rag_service._index = MagicMock()
    rag_service._index.ntotal = 5
    rag_service._index.search = MagicMock(return_value=(np.array([[0.1, 0.2]], dtype=np.float32), np.array([[0, 1]], dtype=np.int64)))
    rag_service._initialized = True

    # Mock DB session and result
    mock_session = AsyncMock()
    mock_doc1 = Document(vector_id=0, content="Content 1", title="Title 1", department="general", source="src1")
    mock_doc2 = Document(vector_id=1, content="Content 2", title="Title 2", department="finance", source="src2")

    # Mock session execution result
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_doc1, mock_doc2]
    mock_session.execute.return_value = mock_result

    # Try patching the one in the module we just imported
    with patch.object(rag_service_module, "async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = mock_session

        results = await rag_service.semantic_search("test query", top_k=2)

        assert len(results) == 2
        assert results[0]["title"] == "Title 1"
        assert results[1]["title"] == "Title 2"
        assert results[0]["score"] > results[1]["score"]

@pytest.mark.asyncio
async def test_add_documents():
    # Reset mocks
    rag_service._index = MagicMock()
    rag_service._index.ntotal = 0
    rag_service._index.add = MagicMock()
    rag_service._initialized = True

    mock_session = AsyncMock()

    documents = [
        {"content": "New content", "title": "New Title", "department": "hr"}
    ]

    with patch.object(rag_service_module, "async_session_factory") as mock_factory:
        mock_factory.return_value.__aenter__.return_value = mock_session
        with patch.object(rag_service, "_save_to_disk", return_value=None):
            count = await rag_service.add_documents(documents)

            assert count == 1
            mock_session.add.assert_called_once()
            mock_session.commit.assert_awaited_once()
            rag_service._index.add.assert_called_once()
