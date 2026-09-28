"""Application configuration using pydantic-settings."""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "AI Restaurant Support & Operations Agent"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database
    DATABASE_URL: str = "sqlite:///./restaurant_agent.db"

    # AI Provider
    AI_PROVIDER: str = "mock"
    OPENAI_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GOOGLE_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # RAG
    VECTOR_STORE_PATH: str = "./vector_store"
    KNOWLEDGE_DOCS_PATH: str = "./data/knowledge"
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 4

    # Agent
    MAX_TOOL_CALLS_PER_REQUEST: int = 5
    TOOL_TIMEOUT_SECONDS: int = 15
    LLM_TIMEOUT_SECONDS: int = 30

    # CORS
    ALLOWED_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]

    # Admin seed
    ADMIN_EMAIL: str = "admin@restaurant.ai"
    ADMIN_PASSWORD: str = "Admin@1234"
    ADMIN_NAME: str = "Restaurant Admin"

    @property
    def is_ai_configured(self) -> bool:
        if self.AI_PROVIDER == "openai":
            return bool(self.OPENAI_API_KEY)
        if self.AI_PROVIDER == "google":
            return bool(self.GOOGLE_API_KEY)
        return self.AI_PROVIDER == "mock"

    @property
    def active_llm_model(self) -> str:
        if self.AI_PROVIDER == "openai":
            return self.OPENAI_MODEL
        if self.AI_PROVIDER == "google":
            return self.GOOGLE_MODEL
        return "mock-fallback"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
