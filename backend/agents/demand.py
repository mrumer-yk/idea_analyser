"""Agent — India Demand-Signal miner.

Searches community sources (Reddit, Quora, forums, Product Hunt) for REAL,
India-relevant pain points and demand signals about the idea, adds them to the
cited evidence pool, then extracts classified signals that quote only those
sources. Fills the gap left by Reddit-research tools and stays India-first.
"""
from __future__ import annotations

import asyncio

from .base import Agent
from .context import Evidence, RunContext
from .prompts import RULES
from .researcher import _classify_source

SYSTEM = RULES + """

Your role: DEMAND-SIGNAL ANALYST. From community discussions (Reddit, Quora,
forums, Product Hunt), surface concrete India-relevant pain points, desires,
and objections in users' own words. Quote/cite only the provided EVIDENCE."""

USER_TMPL = """Idea:
{idea}

COMMUNITY EVIDENCE (cite only these URLs):
{evidence}

Return JSON:
{{
  "demand_signals": [
    {{"observation": "the pain/desire/objection, ideally close to how users phrase it",
      "theme": "short cluster label",
      "sentiment": "pain|desire|objection|neutral",
      "source_url": "a URL from EVIDENCE or null"}}
  ],
  "summary": "1-2 sentences: how strong and specific is real demand evidence in India?"
}}
Prefer signals grounded in a cited community URL. If evidence is weak, say so in the summary and keep the list short and honest."""


class DemandSignalAgent(Agent):
    name = "demand"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Mining community demand signals", None)

        idea = (ctx.state.get("intake", {}) or {}).get("core_idea") or ctx.raw_input or ""
        topic = idea.strip()[:80]
        community = ["reddit.com", "quora.com", "news.ycombinator.com", "producthunt.com"]

        async def _domain_search(q: str):
            try:
                return await ctx.search.search(q, max_results=4, include_domains=community)
            except Exception:
                return []

        async def _open_search(q: str):
            try:
                return await ctx.search.search(q, max_results=3)
            except Exception:
                return []

        batches = await asyncio.gather(
            _domain_search(f"{topic} India problem OR frustration OR complaint"),
            _domain_search(f"{topic} India worth it OR alternative OR recommend"),
            _open_search(f"{topic} India users pain point discussion forum"),
        )

        from ..security import sanitize_external_text

        before = len(ctx.evidence)
        for results in batches:
            ctx.add_evidence([
                Evidence(title=r.title, url=r.url,
                         snippet=sanitize_external_text(r.snippet),
                         source_type=_classify_source(r.url))
                for r in results
            ])
        added = ctx.evidence[before:]
        await ctx.emit(self.name, "info", f"+{len(added)} community sources", {"added": len(added)})

        evidence_block = "\n".join(
            f"- [{e.source_type}] {e.title} | {e.url}\n  {(e.snippet or '')[:400]}"
            for e in added[:20]
        ) or "(no community sources found)"

        result = await self.complete_json(
            ctx, SYSTEM, USER_TMPL.format(idea=topic, evidence=evidence_block), max_tokens=2500
        )
        ctx.state["demand"] = result
        await ctx.emit(
            self.name, "finished",
            f"Found {len(result.get('demand_signals', []))} demand signals", None,
        )
        return result
