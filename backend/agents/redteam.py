"""Agent 8 — Red-Team Critic.

Attacks the thesis: weaknesses, missing evidence, and compliance/regulatory
risks (DPDP Act, RBI/payments, sector-specific). Flags risks; not legal advice.
"""
from __future__ import annotations

from .base import Agent
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: RED-TEAM CRITIC. Be skeptical and specific. Surface what would make
this idea fail in India, what evidence is missing, and compliance/regulatory
risks (e.g. DPDP Act 2023 for data, RBI rules for payments/lending, sector
licensing). Flag risks plainly; this is not legal advice."""

USER_TMPL = """All context so far:
{ctx}

Return JSON:
{{
  "weaknesses": ["the strongest objections to this idea in India"],
  "missing_evidence": ["what we'd need to verify before committing"],
  "risks": [
    {{"risk": "", "type": "market|execution|compliance", "severity": "low|med|high"}}
  ]
}}"""


class RedTeamAgent(Agent):
    name = "redteam"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Running red-team critique", None)
        user = USER_TMPL.format(
            ctx=context_block(
                ctx.state,
                ["intake", "research", "competitors", "segmentation", "sizing", "monetization", "fit"],
            )
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["redteam"] = result
        await ctx.emit(
            self.name, "finished",
            f"Identified {len(result.get('risks', []))} risks", None,
        )
        return result
