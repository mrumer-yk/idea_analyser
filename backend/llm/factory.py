"""Build the configured LLM client from settings."""
from __future__ import annotations

from ..config import Settings, get_settings
from .base import LLMClient


def get_llm_client(settings: Settings | None = None) -> LLMClient:
    settings = settings or get_settings()
    provider = (settings.llm_provider or "azure").lower()

    if provider == "azure":
        from .azure_client import AzureFoundryClient

        return AzureFoundryClient(
            endpoint=settings.azure_foundry_endpoint,
            api_key=settings.azure_foundry_api_key,
            deployment=settings.azure_foundry_deployment,
            api_version=settings.azure_foundry_api_version,
        )

    if provider == "anthropic":
        from .anthropic_client import AnthropicClient

        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_model,
        )

    raise ValueError(f"Unknown LLM_PROVIDER: {provider!r} (expected 'azure' or 'anthropic')")
