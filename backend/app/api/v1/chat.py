"""
Chat API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from core.security import get_current_user
from services.ai_orchestrator import ai_orchestrator
from schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    """
    Send a message to the AI assistant and get a response.
    
    The assistant will:
    1. Search relevant documents using RAG
    2. Execute appropriate tools based on your query
    3. Generate a comprehensive response
    
    Requires authentication.
    """
    try:
        response = ai_orchestrator.handle_query(user, request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/simple")
async def chat_simple(
    payload: dict,
    user: dict = Depends(get_current_user)
):
    """
    Simple chat endpoint for backward compatibility.
    Accepts {"query": "..."} and returns {"answer": "..."}
    """
    query = payload.get("query", "")
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query is required"
        )
    
    request = ChatRequest(query=query)
    response = ai_orchestrator.handle_query(user, request)
    
    return {"answer": response.answer}
