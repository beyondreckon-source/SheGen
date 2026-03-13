"""Application configuration using environment variables."""

import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    groq_api_key: str = ""
    # Alternative LLM (when Groq is restricted) - e.g. TCS genailab
    llm_base_url: str = ""  # e.g. https://genailab.tcs.in/v1
    llm_model: str = ""  # e.g. azure_ai/genailab-maas-DeepSeek-V3-0324
    llm_api_key: str = ""
    ssl_verify: bool = True  # Set False for corporate proxy/SSL issues
    database_url: str = "sqlite+aiosqlite:///./moderation.db"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_url: str = "http://localhost:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
