"""Tavily search adapter.

Tavily is built for agent research: it returns clean, citation-ready content
plus URLs. We map its response onto the generic ``SearchResult``.
"""
from __future__ import annotations

from .base import SearchResult


class TavilyProvider:
    name = "tavily"

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise ValueError("Tavily is not configured: set TAVILY_API_KEY.")
        self._api_key = api_key
        self._client = None  # lazy

    def _ensure_client(self):
        if self._client is None:
            from tavily import AsyncTavilyClient

            self._client = AsyncTavilyClient(api_key=self._api_key)
        return self._client

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        include_domains: list[str] | None = None,
    ) -> list[SearchResult]:
        client = self._ensure_client()
        kwargs = {
            "query": query,
            "max_results": max_results,
            "search_depth": "advanced",
            "include_raw_content": True,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains

        resp = await client.search(**kwargs)
        results: list[SearchResult] = []
        for item in resp.get("results", []):
            results.append(
                SearchResult(
                    title=item.get("title", "") or "",
                    url=item.get("url", "") or "",
                    snippet=item.get("content", "") or "",
                    raw_content=item.get("raw_content"),
                )
            )
        return results
