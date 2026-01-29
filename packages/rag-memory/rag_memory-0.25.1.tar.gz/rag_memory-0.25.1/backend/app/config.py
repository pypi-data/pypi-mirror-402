"""Application configuration using Pydantic settings."""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from functools import lru_cache

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_memory_web"

    # OpenAI
    OPENAI_API_KEY: str

    # LLM Configuration
    LLM_MODEL: str = "gpt-5-mini"
    LLM_TEMPERATURE: float = 1.0

    # Google Search (optional - falls back to DuckDuckGo)
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""

    # Search tool configuration
    GOOGLE_SEARCH_RATE_LIMIT: float = 1.0  # requests per second
    GOOGLE_SEARCH_TIMEOUT: float = 30.0
    DUCKDUCKGO_SEARCH_RATE_LIMIT: float = 1.0
    DUCKDUCKGO_SEARCH_TIMEOUT: float = 30.0
    FETCH_URL_RATE_LIMIT: float = 0.5  # 1 request per 2 seconds
    FETCH_URL_TIMEOUT: float = 15.0
    VALIDATE_URL_TIMEOUT: float = 10.0

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # MCP
    MCP_SERVER_URL: str = "http://localhost:18000/mcp"
    MCP_TIMEOUT: float = 10.0

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
