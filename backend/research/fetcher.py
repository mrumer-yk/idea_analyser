"""Fetch a web page and extract its main readable text.

Used for URL-input ideas (extract product positioning/pricing) and to deepen
research on a promising search result. Uses httpx for the request and
trafilatura for boilerplate-free main-content extraction.
"""
from __future__ import annotations

from dataclasses import dataclass

import httpx

_USER_AGENT = (
    "Mozilla/5.0 (compatible; IdeaValidatorBot/0.1; +https://example.com/bot)"
)
_MAX_CHARS = 20_000


@dataclass
class FetchedPage:
    url: str
    title: str
    text: str
    ok: bool
    error: str | None = None


class PageFetcher:
    def __init__(self, timeout: float = 15.0, max_chars: int = _MAX_CHARS) -> None:
        self._timeout = timeout
        self._max_chars = max_chars

    async def fetch(self, url: str) -> FetchedPage:
        from ..security import is_safe_url

        if not is_safe_url(url):
            return FetchedPage(url=url, title="", text="", ok=False,
                               error="blocked or unsupported URL")
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                headers={"User-Agent": _USER_AGENT},
            ) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                html = resp.text
        except Exception as exc:  # network, status, timeout
            return FetchedPage(url=url, title="", text="", ok=False, error=str(exc))

        title, text = self._extract(html, url)
        if len(text) > self._max_chars:
            text = text[: self._max_chars]
        return FetchedPage(url=url, title=title, text=text, ok=True)

    @staticmethod
    def _extract(html: str, url: str) -> tuple[str, str]:
        import trafilatura

        text = trafilatura.extract(html, include_comments=False, include_tables=True) or ""
        title = ""
        meta = trafilatura.extract_metadata(html)
        if meta and getattr(meta, "title", None):
            title = meta.title
        return title, text
