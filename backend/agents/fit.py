"""Agent 7 — India-Market-Fit Scorer (0-10, weighted factors)."""
from __future__ import annotations

from .base import Agent
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: INDIA-MARKET-FIT SCORER. Score 0-10 using weighted factors:
willingness-to-pay, distribution feasibility, localization need, regulatory
burden, and competitive intensity. Be honest and calibrated."""

USER_TMPL = """All context so far:
{ctx}

Return JSON:
{{
  "india_market_fit": {{
    "score": 0.0,
    "rationale": "why this score, referencing the evidence and analysis",
    "factors": [
      {{"name": "willingness_to_pay", "weight": 0.0, "score": 0.0}},
      {{"name": "distribution", "weight": 0.0, "score": 0.0}},
      {{"name": "localization", "weight": 0.0, "score": 0.0}},
      {{"name": "regulation", "weight": 0.0, "score": 0.0}},
      {{"name": "competition", "weight": 0.0, "score": 0.0}}
    ]
  }}
}}
Weights should sum to ~1.0; the overall score (0-10) should be consistent with the weighted factors."""


class FitAgent(Agent):
    name = "fit"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Scoring India-market fit", None)
        user = USER_TMPL.format(
            ctx=context_block(
                ctx.state,
                ["intake", "research", "competitors", "segmentation", "sizing", "monetization"],
            )
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["fit"] = result
        score = (result.get("india_market_fit", {}) or {}).get("score")
        await ctx.emit(self.name, "finished", f"Fit score: {score}", {"score": score})
        return result
