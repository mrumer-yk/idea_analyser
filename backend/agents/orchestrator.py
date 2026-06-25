"""Sequential agent pipeline.

Runs the 9 agents in order, sharing a RunContext blackboard, then enforces
evidence discipline and renders the markdown report. Each agent failure is
isolated: a crash is logged as an event and the pipeline continues with
whatever state exists (degrade, don't abort), since the synthesizer assembles
from whatever prior agents produced.
"""
from __future__ import annotations

from ..schemas import Report
from ..validators import enforce_evidence_discipline
from .context import RunContext
from .competitor import CompetitorAgent
from .fit import FitAgent
from .intake import IntakeAgent
from .monetization import MonetizationAgent
from .redteam import RedTeamAgent
from .render import render_markdown
from .researcher import ResearcherAgent
from .segmentation import SegmentationAgent
from .sizing import SizingAgent
from .synthesizer import SynthesizerAgent

# Order matters: each agent reads prior agents' state.
PIPELINE = [
    IntakeAgent,
    ResearcherAgent,
    CompetitorAgent,
    SegmentationAgent,
    SizingAgent,
    MonetizationAgent,
    FitAgent,
    RedTeamAgent,
]


def _fragment(name: str, state: dict) -> dict:
    """Map a finished agent's state to a partial-report fragment for live UI."""
    s = state
    if name == "intake":
        return {"idea_summary": (s.get("intake") or {}).get("core_idea", "")}
    if name == "researcher":
        return {"market_signals": (s.get("research") or {}).get("findings", [])}
    if name == "competitor":
        return {"competitors": (s.get("competitors") or {}).get("competitors", [])}
    if name == "segmentation":
        return {"target_segments": (s.get("segmentation") or {}).get("segments", [])}
    if name == "sizing":
        return {"market_size": (s.get("sizing") or {}).get("market_size", {})}
    if name == "monetization":
        m = s.get("monetization") or {}
        return {"revenue_models": m.get("revenue_models", []), "gtm_channels": m.get("gtm_channels", [])}
    if name == "fit":
        return {"india_market_fit": (s.get("fit") or {}).get("india_market_fit", {})}
    if name == "redteam":
        return {"risks": (s.get("redteam") or {}).get("risks", [])}
    return {}


async def run_pipeline(ctx: RunContext) -> dict:
    """Execute the full pipeline; return {report, report_md, violations}."""
    for agent_cls in PIPELINE:
        agent = agent_cls()
        try:
            await agent.run(ctx)
            # Stream this agent's structured output so the UI can fill the
            # report section-by-section instead of waiting for the whole run.
            await ctx.emit(agent.name, "section", "", {"fragment": _fragment(agent.name, ctx.state)})
        except Exception as exc:  # isolate per-agent failure
            await ctx.emit(agent.name, "error", f"agent failed: {exc}", {"error": str(exc)})

    # Synthesizer always runs to assemble whatever we have.
    synth = SynthesizerAgent()
    try:
        await synth.run(ctx)
    except Exception as exc:
        await ctx.emit(synth.name, "error", f"synthesis failed: {exc}", {"error": str(exc)})
        ctx.state["report"] = Report()  # empty but valid

    report: Report = ctx.state.get("report") or Report()
    report, violations = enforce_evidence_discipline(report, ctx.evidence_urls())
    if violations:
        await ctx.emit(
            "validator", "info", f"{len(violations)} evidence-discipline fixes",
            {"violations": violations},
        )

    report_md = render_markdown(report)
    return {"report": report, "report_md": report_md, "violations": violations}
