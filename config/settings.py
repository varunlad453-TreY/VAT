"""
VAT Configuration Settings

Centralized configuration using Pydantic Settings.
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Platform-wide settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Service Identity
    service_name: str = Field(default="vat-service", description="Service name")
    environment: str = Field(default="development", description="Runtime environment")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Server
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8000,*",
        description="Comma-separated allowed CORS origins",
    )

    # PostgreSQL Database
    postgres_host: str = Field(default="localhost", description="PostgreSQL host")
    postgres_port: int = Field(default=5432, description="PostgreSQL port")
    postgres_user: str = Field(default="vat", description="PostgreSQL user")
    postgres_password: str = Field(default="vat_password", description="PostgreSQL password")
    postgres_database: str = Field(default="vat", description="PostgreSQL database")
    database_url: Optional[str] = Field(
        default=None, description="Full PostgreSQL connection URL (overrides individual params if set)"
    )

    # Vector Embedding Settings
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="SentenceTransformer model name")
    embedding_dimension: int = Field(default=384, description="Vector dimension size")
    embedding_service_url: str = Field(
        default="http://localhost:8001",
        description="URL of dedicated standalone embedding microservice",
    )
    embedding_timeout_seconds: float = Field(
        default=2.0,
        description="HTTP request timeout for remote embedding microservice in seconds",
    )
    embedding_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts with exponential backoff via tenacity",
    )

    # LLM Settings (GitHub Models / OpenAI API)
    github_token: str = Field(default="", description="GitHub token for GitHub Models API")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    ai_model: str = Field(default="gpt-4o-mini", description="LLM model name")
    ai_base_url: str = Field(
        default="https://models.inference.ai.azure.com", description="Base URL for LLM inference"
    )

    @property
    def pg_url(self) -> str:
        """Constructs asyncpg-compatible PostgreSQL URL."""
        if self.database_url:
            return self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"

    @property
    def cors_origins_list(self) -> List[str]:
        """Parsed list of allowed CORS origins."""
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Returns the cached Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


settings = get_settings()
