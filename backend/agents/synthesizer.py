"""Agent 9 — Synthesizer.

Assembles the final Report. Structured sections are taken deterministically
from prior agents' state (grounded, no re-hallucination); the LLM only writes
the narrative summary and the final recommendation/confidence.
"""
from __future__ import annotations

from ..schemas import Report
from .base import Agent
from .context import RunContext
from .prompts import RULES, context_block

SYSTEM = RULES + """

Your role: SENIOR PRODUCT STRATEGIST writing the executive verdict. Base your
recommendation strictly on the analysis provided."""

USER_TMPL = """Full analysis:
{ctx}

Write the executive verdict. Return JSON:
{{
  "idea_summary": "2-3 sentences",
  "problem_and_pain": "the core user problem and how acute it is in India",
  "recommendation": "pursue|pivot|reject",
  "confidence": "low|medium|high"
}}
Recommendation must be consistent with the India-market-fit score and red-team risks."""


def _coerce_list(value) -> list:
    return value if isinstance(value, list) else []


class SynthesizerAgent(Agent):
    name = "synthesizer"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Synthesizing final report", None)

        verdict = await self.complete_json(
            ctx,
            SYSTEM,
            USER_TMPL.format(
                ctx=context_block(
                    ctx.state,
                    ["intake", "research", "demand", "competitors", "segmentation",
                     "sizing", "monetization", "fit", "redteam", "pivots"],
                )
            ),
            max_tokens=1500,
        )

        s = ctx.state
        report = Report.model_validate(
            {
                "idea_summary": verdict.get("idea_summary", "")
                or (s.get("intake", {}) or {}).get("core_idea", ""),
                "problem_and_pain": verdict.get("problem_and_pain", ""),
                "india_market_fit": (s.get("fit", {}) or {}).get("india_market_fit", {}),
                "target_segments": _coerce_list((s.get("segmentation", {}) or {}).get("segments")),
                "competitors": _coerce_list((s.get("competitors", {}) or {}).get("competitors")),
                # prefer cross-validated signals (carry verification) over raw findings
                "market_signals": _coerce_list(
                    (s.get("verification", {}) or {}).get("signals")
                    or (s.get("research", {}) or {}).get("findings")
                ),
                "demand_signals": _coerce_list((s.get("demand", {}) or {}).get("demand_signals")),
                "market_size": (s.get("sizing", {}) or {}).get("market_size", {}),
                "revenue_models": _coerce_list((s.get("monetization", {}) or {}).get("revenue_models")),
                "gtm_channels": _coerce_list((s.get("monetization", {}) or {}).get("gtm_channels")),
                "risks": _coerce_list((s.get("redteam", {}) or {}).get("risks")),
                "pivots": _coerce_list((s.get("pivots", {}) or {}).get("pivots")),
                "recommendation": verdict.get("recommendation", "pivot"),
                "confidence": verdict.get("confidence", "low"),
                "sources": [
                    {"title": e.title, "url": e.url, "source_type": e.source_type}
                    for e in ctx.evidence
                ],
            }
        )
        ctx.state["report"] = report
        await ctx.emit(
            self.name, "finished",
            f"Report ready: {report.recommendation}",
            {"recommendation": report.recommendation, "confidence": report.confidence},
        )
        return {"report": report}
