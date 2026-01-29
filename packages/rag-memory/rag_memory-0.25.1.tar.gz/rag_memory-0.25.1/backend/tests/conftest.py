"""
Shared pytest fixtures for backend tests.

Provides database fixtures, test client, and factory functions.
"""

import sys
from pathlib import Path

# Add backend directory to Python path so 'from app.' imports work
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for fast tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Create async engine for test database."""
    return create_async_engine(TEST_DATABASE_URL, echo=False)


@pytest_asyncio.fixture
async def db_session(engine):
    """Provide isolated database session per test."""
    from app.rag.models import Base

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    # Drop all tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Async test client with database override."""
    from app.main import app
    from app.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_conversation(db_session):
    """Factory to create test conversations."""
    from app.rag.models import Conversation

    async def _create(title="Test Conversation"):
        conv = Conversation(title=title)
        db_session.add(conv)
        await db_session.commit()
        await db_session.refresh(conv)
        return conv

    return _create


@pytest_asyncio.fixture
async def create_message(db_session):
    """Factory to create test messages."""
    from app.rag.models import Message

    async def _create(conversation_id: int, role: str, content: str):
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        db_session.add(msg)
        await db_session.commit()
        await db_session.refresh(msg)
        return msg

    return _create


@pytest_asyncio.fixture
async def create_starter_prompt(db_session):
    """Factory to create test starter prompts."""
    from app.rag.models import StarterPrompt

    async def _create(prompt_text: str, category: str = None, order: int = 0):
        sp = StarterPrompt(
            prompt_text=prompt_text,
            category=category,
            display_order=order,
        )
        db_session.add(sp)
        await db_session.commit()
        await db_session.refresh(sp)
        return sp

    return _create
