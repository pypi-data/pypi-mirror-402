"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .rag.router import router as rag_router
from .rag.mcp_proxy import router as mcp_proxy_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

settings = get_settings()


def run_migrations():
    """Run Alembic migrations on startup.

    This ensures the database schema is always up-to-date, whether:
    - Clean stack (new database with no tables)
    - Existing stack with new migrations to apply
    - Already up-to-date (no-op)

    Alembic tracks applied revisions in `alembic_version` table.
    """
    from alembic.config import Config
    from alembic import command

    # Find alembic.ini relative to this file
    backend_dir = Path(__file__).parent.parent
    alembic_ini = backend_dir / "alembic.ini"

    if not alembic_ini.exists():
        logger.error(f"alembic.ini not found at {alembic_ini}")
        raise RuntimeError(f"Cannot run migrations: alembic.ini not found at {alembic_ini}")

    logger.info(f"Running database migrations from {alembic_ini}")

    alembic_cfg = Config(str(alembic_ini))
    # Override script_location to be relative to backend dir
    alembic_cfg.set_main_option("script_location", str(backend_dir / "alembic"))

    # Run migrations to head
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations complete")

    # Setup LangGraph checkpointer tables (idempotent - uses setup_checkpointer())
    from langgraph.checkpoint.postgres import PostgresSaver
    import psycopg
    from .config import get_settings
    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql")
    with psycopg.connect(sync_url) as conn:
        checkpointer = PostgresSaver(conn)
        checkpointer.setup()
    logger.info("LangGraph checkpoint tables ready")


async def seed_starter_prompts():
    """Seed starter prompts if missing (idempotent).

    This ensures starter prompts exist on every startup.
    Safe to run multiple times - only inserts if table is empty.
    """
    from sqlalchemy import select
    from .database import async_session_maker
    from .rag.models import StarterPrompt

    STARTER_PROMPTS = [
        {"prompt_text": "What collections do I have?", "category": "exploration", "has_placeholder": False, "display_order": 1},
        {"prompt_text": "Search my knowledge base for [topic]", "category": "search", "has_placeholder": True, "display_order": 2},
        {"prompt_text": "Show me what's in the [collection name] collection", "category": "exploration", "has_placeholder": True, "display_order": 3},
        {"prompt_text": "What topics are covered in my knowledge base?", "category": "exploration", "has_placeholder": False, "display_order": 4},
        {"prompt_text": "How has my understanding of [topic] evolved?", "category": "analysis", "has_placeholder": True, "display_order": 5},
        {"prompt_text": "What's the relationship between [concept A] and [concept B]?", "category": "analysis", "has_placeholder": True, "display_order": 6},
        {"prompt_text": "What's new about [topic] that I might not know yet?", "category": "analysis", "has_placeholder": True, "display_order": 7},
    ]

    async with async_session_maker() as db:
        result = await db.execute(select(StarterPrompt))
        existing = result.scalars().all()

        if existing:
            logger.info(f"Starter prompts already exist ({len(existing)} found)")
            return

        logger.info(f"Seeding {len(STARTER_PROMPTS)} starter prompts...")
        for prompt_data in STARTER_PROMPTS:
            db.add(StarterPrompt(**prompt_data))
        await db.commit()
        logger.info("Starter prompts seeded successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting RAG Memory web application...")
    logger.info(f"Database: {settings.DATABASE_URL}")

    # Auto-apply migrations on every startup
    # This handles: clean stack, new migrations, or already up-to-date
    run_migrations()

    # Seed starter prompts if missing (idempotent)
    await seed_starter_prompts()

    yield

    # Shutdown
    logger.info("Shutting down RAG Memory web application...")


# Create FastAPI app
app = FastAPI(
    title="RAG Memory Web",
    description="Web interface for RAG Memory knowledge base management",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
origins = settings.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(rag_router)
app.include_router(mcp_proxy_router)

logger.info("RAG Memory web application initialized")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RAG Memory Web API",
        "version": "0.1.0",
        "docs": "/docs",
    }
