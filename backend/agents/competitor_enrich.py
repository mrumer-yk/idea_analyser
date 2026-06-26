"""Agent — Competitor Enrichment (competitive intelligence).

For each top competitor, runs a targeted search for funding, founding year,
scale (users/employees), ratings, and a named weakness/gap, then fills those
fields citing only retrieved evidence. Turns the competitor list into a real
competitive-intelligence grid (matching the depth of leading validators).
"""
from __future__ import annotations

import asyncio

from .base import Agent
from .context import Evidence, RunContext
from .prompts import RULES
from .researcher import _classify_source

SYSTEM = RULES + """

Your role: COMPETITIVE INTELLIGENCE analyst. Enrich each competitor with
funding, founding year, scale, rating, and a specific exploitable weakness/gap.
Use ONLY the gathered evidence; if a fact isn't in evidence, leave that field
empty rather than guessing. Prefer India-relevant data."""

USER_TMPL = """Competitors to enrich:
{competitors}

EVIDENCE gathered for these competitors (cite only these URLs):
{evidence}

Return JSON echoing every competitor with enrichment added:
{{
  "competitors": [
    {{"name": "", "type": "direct|indirect", "positioning": "", "pricing": "", "url": "",
      "funding": "stage + amount raised, or ''",
      "founded": "year or ''",
      "scale": "users/MAU/employees signal, or ''",
      "rating": "G2/Play Store rating + review count, or ''",
      "weakness": "one specific weakness or exploitable gap, or ''"}}
  ]
}}
Keep name/type/positioning/pricing/url as given. Leave any unknown enrichment field as ''."""


class CompetitorEnrichAgent(Agent):
    name = "competitor_enrich"

    async def run(self, ctx: RunContext) -> dict:
        competitors = (ctx.state.get("competitors", {}) or {}).get("competitors") or []
        competitors = [c for c in competitors if isinstance(c, dict) and c.get("name")][:6]
        if not competitors:
            await ctx.emit(self.name, "finished", "No competitors to enrich", None)
            return {"competitors": []}

        await ctx.emit(self.name, "started", f"Enriching {len(competitors)} competitors", None)

        from ..security import sanitize_external_text

        async def _intel(name: str):
            try:
                return await ctx.search.search(
                    f"{name} India funding founded users rating reviews", max_results=3
                )
            except Exception:
                return []

        batches = await asyncio.gather(*[_intel(c["name"]) for c in competitors])
        before = len(ctx.evidence)
        for results in batches:
            ctx.add_evidence([
                Evidence(title=r.title, url=r.url,
                         snippet=sanitize_external_text(r.snippet),
                         source_type=_classify_source(r.url))
                for r in results
            ])
        new_ev = ctx.evidence[before:]

        import json as _json
        comp_block = _json.dumps(competitors, ensure_ascii=False)[:4000]
        evidence_block = "\n".join(
            f"- {e.title} | {e.url}\n  {(e.snippet or '')[:300]}" for e in new_ev[:24]
        ) or "(no competitor intel found)"

        result = await self.complete_json(
            ctx, SYSTEM,
            USER_TMPL.format(competitors=comp_block, evidence=evidence_block),
            max_tokens=3000,
        )
        enriched = result.get("competitors") or competitors
        # write back so the synthesizer + fragment use the enriched list
        ctx.state.setdefault("competitors", {})["competitors"] = enriched

        n_enriched = sum(1 for c in enriched if c.get("funding") or c.get("founded") or c.get("rating"))
        await ctx.emit(
            self.name, "finished", f"Enriched {n_enriched}/{len(enriched)} with intel", None,
        )
        return result
