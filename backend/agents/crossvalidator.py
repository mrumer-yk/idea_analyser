"""Agent — Cross-Validator.

Independently re-searches the most important factual claims to corroborate them
with a SECOND source, then tags each verified / unverified / conflicting and
downgrades numeric 'fact' claims that can't be corroborated. This is the
trust-defining step: a claim survives only if independent evidence agrees.
"""
from __future__ import annotations

import asyncio

from .base import Agent
from .context import Evidence, RunContext
from .prompts import RULES
from .researcher import _classify_source

SYSTEM = RULES + """

Your role: CROSS-VALIDATOR / fact-checker. For each candidate claim you are
given the original source plus freshly-gathered CORROBORATION evidence from
independent searches. Judge each claim:
- verified: an INDEPENDENT second source (different domain) supports it
- conflicting: sources disagree or contradict it
- unverified: only the original source supports it, or no corroboration found
Be strict. Default to 'unverified' when unsure. A numeric claim marked 'fact'
that you cannot verify must be downgraded to classification 'hypothesis'."""

USER_TMPL = """Candidate claims to verify (with their original source):
{claims}

CORROBORATION EVIDENCE gathered from independent searches (cite these URLs):
{evidence}

Return JSON:
{{
  "signals": [
    {{"claim": "<echo the claim>",
      "classification": "fact|assumption|hypothesis",
      "source_url": "original source url or null",
      "verification": "verified|unverified|conflicting",
      "corroborating_url": "an INDEPENDENT second url from the evidence (different domain) or null"}}
  ],
  "summary": "1-2 sentences on overall evidence strength after cross-checking"
}}
Keep the same claims; only set verification, corroborating_url, and downgrade classification where unverifiable."""


def _domain(url: str | None) -> str:
    if not url:
        return ""
    u = url.lower().split("//")[-1]
    return u.split("/")[0].replace("www.", "")


class CrossValidatorAgent(Agent):
    name = "crossvalidator"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Cross-checking key claims", None)

        findings = (ctx.state.get("research", {}) or {}).get("findings") or []
        # Prioritize factual claims; verify the top handful (cost guard).
        claims = [f for f in findings if isinstance(f, dict) and f.get("claim")]
        claims.sort(key=lambda f: 0 if f.get("classification") == "fact" else 1)
        claims = claims[:6]
        if not claims:
            ctx.state["verification"] = {"signals": [], "summary": "No claims to verify."}
            await ctx.emit(self.name, "finished", "No claims to verify", None)
            return ctx.state["verification"]

        from ..security import sanitize_external_text

        async def _corroborate(claim: str):
            try:
                return await ctx.search.search(f"{claim} India", max_results=3)
            except Exception:
                return []

        batches = await asyncio.gather(*[_corroborate(c["claim"][:120]) for c in claims])
        before = len(ctx.evidence)
        for results in batches:
            ctx.add_evidence([
                Evidence(title=r.title, url=r.url,
                         snippet=sanitize_external_text(r.snippet),
                         source_type=_classify_source(r.url))
                for r in results
            ])
        new_ev = ctx.evidence[before:]

        claims_block = "\n".join(
            f"- claim: {c['claim']}\n  original_source: {c.get('source_url')}\n  classification: {c.get('classification')}"
            for c in claims
        )
        evidence_block = "\n".join(
            f"- [{_domain(e.url)}] {e.title} | {e.url}\n  {(e.snippet or '')[:300]}"
            for e in new_ev[:24]
        ) or "(no corroboration found)"

        result = await self.complete_json(
            ctx, SYSTEM,
            USER_TMPL.format(claims=claims_block, evidence=evidence_block),
            max_tokens=2500,
        )

        # Safety net: enforce independence (corroborating domain must differ from source).
        for s in result.get("signals", []):
            if s.get("corroborating_url") and _domain(s["corroborating_url"]) == _domain(s.get("source_url")):
                s["corroborating_url"] = None
                if s.get("verification") == "verified":
                    s["verification"] = "unverified"

        ctx.state["verification"] = result
        verified = sum(1 for s in result.get("signals", []) if s.get("verification") == "verified")
        await ctx.emit(
            self.name, "finished",
            f"{verified}/{len(result.get('signals', []))} claims verified",
            {"verified": verified},
        )
        return result
