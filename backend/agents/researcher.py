"""Agent 2 — Market Researcher.

Executes the intake's India-biased search queries against the search provider,
optionally deepens a few high-value results by fetching the page, builds the
shared evidence pool, then asks the LLM to extract classified findings that
cite ONLY the gathered evidence.
"""
from __future__ import annotations

import asyncio

from .base import Agent, render_evidence
from .context import Evidence, RunContext
from .prompts import RULES

SYSTEM = RULES + """

Your role: MARKET RESEARCHER. Summarize findings about the Indian market,
citing only URLs from the EVIDENCE list."""

USER_TMPL = """Idea context:
{idea}

EVIDENCE (cite only these URLs):
{evidence}

Return a JSON object:
{{
  "findings": [
    {{"claim": "specific finding about the India market/demand/competition",
      "classification": "fact|assumption|hypothesis",
      "source_url": "a URL from EVIDENCE or null"}}
  ],
  "summary": "3-5 sentence synthesis of what the evidence says about India-market viability"
}}
A finding may be 'fact' ONLY if backed by a cited EVIDENCE url."""


def _classify_source(url: str) -> str:
    u = (url or "").lower()
    if any(k in u for k in ["pricing", "/plans", "/price"]):
        return "pricing"
    if any(k in u for k in [".gov.in", "rbi.org", "trai.gov", "meity", "sebi.gov"]):
        return "gov"
    if "play.google.com" in u or "apps.apple.com" in u:
        return "appstore"
    if any(k in u for k in [
        "linkedin.com", "youtube.com", "youtu.be", "twitter.com", "x.com",
        "facebook.com", "instagram.com",
    ]):
        return "social"
    if any(k in u for k in ["reddit.com", "quora.com", "ycombinator", "forum"]):
        return "forum"
    if any(k in u for k in [
        "marketsandmarkets", "grandviewresearch", "imarc", "mordorintelligence",
        "researchandmarkets", "market.us", "statista", "expertmarketresearch",
        "fortunebusinessinsights", "alliedmarketresearch", "marketresearch",
        "marketdataforecast", "precedenceresearch", "marketsize", "cagr",
    ]):
        return "research"
    if any(k in u for k in [
        "economictimes", "livemint", "yourstory", "inc42", "moneycontrol",
        "business-standard", "thehindu", "ndtv", "/news", "news.",
    ]):
        return "news"
    if "/blog" in u or "blog." in u:
        return "blog"
    return "other"


class ResearcherAgent(Agent):
    name = "researcher"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Searching Indian market sources", None)
        queries = (ctx.state.get("intake", {}) or {}).get("search_queries") or []
        queries = [q for q in queries if isinstance(q, str)][:8]
        if not queries:
            idea = (ctx.state.get("intake", {}) or {}).get("core_idea", "")
            queries = [f"{idea} India", f"{idea} competitors India pricing"]

        # Fan out searches concurrently.
        async def _do(q: str):
            try:
                return await ctx.search.search(q, max_results=4)
            except Exception as exc:  # degrade, don't crash the run
                await ctx.emit(self.name, "info", f"search failed: {q}", {"error": str(exc)})
                return []

        batches = await asyncio.gather(*[_do(q) for q in queries])

        from ..security import sanitize_external_text

        for results in batches:
            ctx.add_evidence(
                [
                    Evidence(
                        title=r.title, url=r.url,
                        snippet=sanitize_external_text(r.snippet),
                        source_type=_classify_source(r.url),
                    )
                    for r in results
                ]
            )
        await ctx.emit(
            self.name, "info", f"Gathered {len(ctx.evidence)} sources",
            {"count": len(ctx.evidence)},
        )

        # Deepen a few promising sources within fetch budget.
        to_fetch = [e for e in ctx.evidence if not e.snippet or len(e.snippet) < 120]
        from ..security import sanitize_external_text

        for e in to_fetch[: ctx.fetch_budget]:
            page = await ctx.fetcher.fetch(e.url)
            if page.ok and page.text:
                e.snippet = sanitize_external_text(page.text[:600])

        idea_ctx = (ctx.state.get("intake", {}) or {})
        user = USER_TMPL.format(
            idea=str({k: idea_ctx.get(k) for k in ["core_idea", "business_hypothesis"]}),
            evidence=render_evidence(ctx),
        )
        result = await self.complete_json(ctx, SYSTEM, user, max_tokens=3000)
        ctx.state["research"] = result
        await ctx.emit(
            self.name, "finished",
            f"Extracted {len(result.get('findings', []))} findings",
            {"sources": len(ctx.evidence)},
        )
        return result
