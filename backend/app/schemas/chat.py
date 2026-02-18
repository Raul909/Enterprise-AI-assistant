"""
Pydantic schemas for chat request/response.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's question or query"
    )
    conversation_id: str | None = Field(
        default=None,
        description="Unique identifier for conversation continuity"
    )
    include_sources: bool = Field(
        default=True,
        description="Whether to include source references in response"
    )
    max_tokens: int | None = Field(
        default=None,
        ge=100,
        le=4000,
        description="Maximum tokens in response"
    )


class ToolExecution(BaseModel):
    """Schema for a single tool execution result."""
    
    tool_name: str
    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time_ms: float


class SourceReference(BaseModel):
    """Schema for source document references."""
    
    title: str
    content_snippet: str
    source_type: str  # "document", "database", "github", "jira"
    url: str | None = None
    relevance_score: float


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    
    answer: str
    conversation_id: str
    sources: list[SourceReference] = Field(default_factory=list)
    tools_used: list[ToolExecution] = Field(default_factory=list)
    processing_time_ms: float
    model_used: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())


class ChatStreamChunk(BaseModel):
    """Schema for streaming response chunks."""
    
    chunk_type: str  # "text", "source", "tool", "done", "error"
    content: str | dict
    conversation_id: str


class ConversationMessage(BaseModel):
    """Schema for a message in conversation history."""
    
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    sources: list[SourceReference] = Field(default_factory=list)


class ConversationHistory(BaseModel):
    """Schema for conversation history."""
    
    conversation_id: str
    messages: list[ConversationMessage]
    created_at: datetime
    updated_at: datetime


class ConversationContext(BaseModel):
    """Holds context for a conversation."""
    conversation_id: str
    messages: list[dict[str, str]] = Field(default_factory=list)
    tools_used: list[ToolExecution] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)
