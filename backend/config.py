"""Application configuration, loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Provider selection
    llm_provider: str = "azure"  # "azure" | "anthropic"

    # Azure AI Foundry (OpenAI-compatible)
    azure_foundry_endpoint: str = ""
    azure_foundry_api_key: str = ""
    azure_foundry_deployment: str = ""
    azure_foundry_api_version: str = "2024-10-21"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # Research
    tavily_api_key: str = ""
    max_fetch_per_run: int = 8

    # Cap on concurrent LLM calls across ALL in-flight runs (rate-limit guard)
    max_concurrent_llm: int = 8

    # App
    database_path: str = "./data/app.db"
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
