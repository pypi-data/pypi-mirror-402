"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Conversation schemas
class ConversationBase(BaseModel):
    """Base conversation schema."""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: int
    is_pinned: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    conversation_ids: list[int]


# Message schemas
class MessageBase(BaseModel):
    """Base message schema."""
    role: str  # "user" or "assistant"
    content: str


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: int


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Chat request/response
class ChatRequest(BaseModel):
    """Schema for chat request."""
    message: str
    conversation_id: Optional[int] = None  # If None, creates new conversation


class ChatResponse(BaseModel):
    """Schema for chat response (non-streaming)."""
    conversation_id: int
    response: str


# Starter prompt schemas
class StarterPromptResponse(BaseModel):
    """Schema for starter prompt response."""
    id: int
    prompt_text: str
    category: Optional[str]
    has_placeholder: bool
    display_order: int

    class Config:
        from_attributes = True


# Tool approval schemas
class ToolApprovalRequest(BaseModel):
    """Schema for approving pending tool calls."""
    conversation_id: int


class ToolRejectionRequest(BaseModel):
    """Schema for rejecting pending tool calls."""
    conversation_id: int
    reason: Optional[str] = None  # Optional reason for rejection


class RevisedToolCall(BaseModel):
    """Schema for a single revised tool call."""
    id: str
    name: str
    args: dict


class ToolRevisionRequest(BaseModel):
    """Schema for revising and resuming tool calls."""
    conversation_id: int
    tools: list[RevisedToolCall]
