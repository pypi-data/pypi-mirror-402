"""Database models for RAG Memory web application."""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base


class Conversation(Base):
    """Conversation model for storing chat sessions."""

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=True)  # Optional title
    is_pinned = Column(Boolean, default=False, nullable=False)  # Pin to top of sidebar
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    """Message model for storing individual chat messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class StarterPrompt(Base):
    """Starter prompt suggestions for empty chat state."""

    __tablename__ = "starter_prompts"

    id = Column(Integer, primary_key=True, index=True)
    prompt_text = Column(Text, nullable=False)  # e.g., "What collections do I have?"
    category = Column(String(50), nullable=True)  # "exploration", "search", "analysis"
    has_placeholder = Column(Boolean, default=False)  # True if contains [topic], [collection], etc.
    display_order = Column(Integer, nullable=False, default=0)  # Order to display prompts
    created_at = Column(DateTime(timezone=True), server_default=func.now())
