"""Build the configured search provider from settings."""
from __future__ import annotations

from ..config import Settings, get_settings
from .base import SearchProvider


def get_search_provider(settings: Settings | None = None) -> SearchProvider:
    settings = settings or get_settings()
    from .tavily import TavilyProvider

    return TavilyProvider(api_key=settings.tavily_api_key)
