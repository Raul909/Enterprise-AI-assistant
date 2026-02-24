"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables with sensible defaults.
"""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Enterprise AI Assistant"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    
    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/enterprise_ai"
    database_echo: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str:
        """Ensure database URL uses async driver."""
        if not v:
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and "+asyncpg" not in v:
             return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # JWT Authentication
    jwt_secret_key: str = "your-super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7
    
    # Anthropic (alternative)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    
    # AI Provider selection
    ai_provider: Literal["openai", "anthropic"] = "openai"
    
    # MCP Server
    mcp_server_url: str = "http://localhost:3333"
    mcp_timeout_seconds: int = 30
    
    # Vector Store
    vector_store_path: str = "./vector-store"
    embedding_model: str = "all-MiniLM-L6-v2"
    vector_search_top_k: int = 5
    
    # Redis (optional caching)
    redis_url: str | None = None
    cache_ttl_seconds: int = 3600
    
    # Rate Limiting
    login_rate_limit_count: int = 5
    login_rate_limit_window: int = 60

    # Logging
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Convenience alias
settings = get_settings()
