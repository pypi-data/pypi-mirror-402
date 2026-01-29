"""FastAPI router for RAG Memory web application.

Provides:
- SSE chat endpoint for streaming agent responses
- REST endpoints for conversations, messages, starter prompts
"""

import logging
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..shared.agent_factory import create_rag_memory_agent
from ..shared.chat_bridge import (
    stream_chat_response,
    resume_after_approval,
    reject_tool_proposal,
    revise_and_resume,
)
from .models import Conversation, Message, StarterPrompt
from .schemas import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageResponse,
    ChatRequest,
    StarterPromptResponse,
    BulkDeleteRequest,
    ToolApprovalRequest,
    ToolRejectionRequest,
    ToolRevisionRequest,
)

router = APIRouter(prefix="/api", tags=["rag"])
logger = logging.getLogger(__name__)

# Global agent instance (created on first request)
_agent = None


async def get_agent():
    """Get or create agent instance."""
    global _agent
    if _agent is None:
        logger.info("Creating agent for first time...")
        _agent = await create_rag_memory_agent()
    return _agent


# ============================================================================
# Chat Endpoints
# ============================================================================

@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
):
    """
    Stream chat response via SSE.

    Accepts a message and optional conversation_id. If conversation_id not provided,
    creates a new conversation. Streams agent response token-by-token.
    """
    from ..database import async_session_maker

    logger.info(f"Chat stream request: conversation_id={request.conversation_id}")

    # Create/get conversation in separate session
    async with async_session_maker() as db:
        if request.conversation_id:
            # Load existing conversation
            result = await db.execute(
                select(Conversation).where(Conversation.id == request.conversation_id)
            )
            conversation = result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            conversation_id = conversation.id

        else:
            # Create new conversation
            conversation = Conversation(title=f"Chat at {datetime.utcnow()}")
            db.add(conversation)
            await db.flush()  # Get ID
            await db.commit()
            conversation_id = conversation.id
            logger.info(f"Created new conversation {conversation_id}")

    # Get agent
    agent = await get_agent()

    # Stream response (manages its own DB session)
    return StreamingResponse(
        stream_chat_response(
            agent=agent,
            user_message=request.message,
            conversation_id=conversation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    )


@router.post("/chat/approve")
async def approve_tool_execution(
    request: ToolApprovalRequest,
):
    """
    Approve pending tool calls and resume agent execution.

    Called when user clicks "Approve" on a tool proposal.
    """
    logger.info(f"Tool approval request for conversation {request.conversation_id}")

    agent = await get_agent()

    return StreamingResponse(
        resume_after_approval(
            agent=agent,
            conversation_id=request.conversation_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/reject")
async def reject_tool_execution(
    request: ToolRejectionRequest,
):
    """
    Reject pending tool calls.

    Called when user clicks "Reject" on a tool proposal.
    Injects a rejection message and lets agent respond.
    """
    logger.info(f"Tool rejection request for conversation {request.conversation_id}")

    agent = await get_agent()

    return StreamingResponse(
        reject_tool_proposal(
            agent=agent,
            conversation_id=request.conversation_id,
            rejection_reason=request.reason,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/chat/revise")
async def revise_tool_execution(
    request: ToolRevisionRequest,
):
    """
    Revise pending tool call arguments and resume.

    Called when user modifies tool arguments in the approval UI.
    """
    logger.info(f"Tool revision request for conversation {request.conversation_id}")

    agent = await get_agent()

    # Convert Pydantic models to dicts
    revised_tools = [tool.dict() for tool in request.tools]

    return StreamingResponse(
        revise_and_resume(
            agent=agent,
            conversation_id=request.conversation_id,
            revised_tools=revised_tools,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ============================================================================
# Conversation Endpoints
# ============================================================================

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    conversation: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new conversation."""
    db_conversation = Conversation(**conversation.dict())
    db.add(db_conversation)
    await db.commit()
    await db.refresh(db_conversation)
    return db_conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all conversations."""
    result = await db.execute(
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    conversations = result.scalars().all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific conversation."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    update_data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update conversation (rename, pin/unpin)."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Update fields if provided
    if update_data.title is not None:
        conversation.title = update_data.title
    if update_data.is_pinned is not None:
        conversation.is_pinned = update_data.is_pinned

    await db.commit()
    await db.refresh(conversation)

    return conversation


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a conversation and all its messages."""
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conversation)
    await db.commit()

    return {"status": "deleted", "conversation_id": conversation_id}


@router.post("/conversations/bulk-delete")
async def bulk_delete_conversations(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db),
):
    """Delete multiple conversations at once."""
    if not request.conversation_ids:
        return {"status": "success", "deleted_count": 0}

    result = await db.execute(
        select(Conversation).where(Conversation.id.in_(request.conversation_ids))
    )
    conversations = result.scalars().all()

    for conversation in conversations:
        await db.delete(conversation)

    await db.commit()

    return {
        "status": "success",
        "deleted_count": len(conversations),
        "conversation_ids": [c.id for c in conversations],
    }


@router.delete("/conversations/all")
async def delete_all_conversations(
    db: AsyncSession = Depends(get_db),
):
    """Delete ALL conversations. Use with caution."""
    result = await db.execute(select(Conversation))
    conversations = result.scalars().all()

    count = len(conversations)

    for conversation in conversations:
        await db.delete(conversation)

    await db.commit()

    return {"status": "success", "deleted_count": count}


# ============================================================================
# Message Endpoints
# ============================================================================

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get all messages for a conversation."""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return messages


# ============================================================================
# Starter Prompts Endpoints
# ============================================================================

@router.get("/starter-prompts", response_model=List[StarterPromptResponse])
async def get_starter_prompts(
    db: AsyncSession = Depends(get_db),
):
    """Get all starter prompts ordered by display_order."""
    result = await db.execute(
        select(StarterPrompt).order_by(StarterPrompt.display_order.asc())
    )
    prompts = result.scalars().all()
    return prompts


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
