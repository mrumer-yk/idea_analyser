"""Render a validated Report into the markdown sections the user requires."""
from __future__ import annotations

from ..schemas import Report


def render_markdown(report: Report) -> str:
    r = report
    out: list[str] = []
    a = out.append

    a("# India Market Validation Report\n")

    a("## Idea Summary")
    a(r.idea_summary or "_n/a_")

    a("\n## Problem & User Pain")
    a(r.problem_and_pain or "_n/a_")

    fit = r.india_market_fit
    a(f"\n## India Market Fit Score: {fit.score}/10")
    a(fit.rationale or "")
    if fit.factors:
        a("\n| Factor | Weight | Score |")
        a("|---|---|---|")
        for f in fit.factors:
            a(f"| {f.name} | {f.weight} | {f.score} |")

    a("\n## Target Customer Segments")
    for seg in r.target_segments:
        a(f"\n**{seg.segment}** — {seg.persona}")
        if seg.pains:
            a("- Pains: " + "; ".join(seg.pains))
        if seg.jtbd:
            a("- Jobs-to-be-done: " + "; ".join(seg.jtbd))

    a("\n## Competitor Landscape")
    if r.competitors:
        a("\n| Competitor | Type | Positioning | Pricing | Link |")
        a("|---|---|---|---|---|")
        for c in r.competitors:
            link = f"[link]({c.url})" if c.url else ""
            a(f"| {c.name} | {c.type} | {c.positioning} | {c.pricing} | {link} |")
    else:
        a("_No competitors identified._")

    a("\n## Market Signals & Evidence")
    for sig in r.market_signals:
        src = f" — [source]({sig.source_url})" if sig.source_url else ""
        a(f"- _({sig.classification})_ {sig.claim}{src}")

    ms = r.market_size
    a("\n## Market Size (TAM / SAM / SOM)")
    a(f"- **TAM:** {ms.tam or 'n/a'}")
    a(f"- **SAM:** {ms.sam or 'n/a'}")
    a(f"- **SOM:** {ms.som or 'n/a'}")
    a(f"- **Grounded:** {ms.grounded}")
    if ms.assumptions:
        a("- Assumptions:")
        for x in ms.assumptions:
            a(f"  - {x}")

    a("\n## Revenue Model Options")
    for rm in r.revenue_models:
        a(f"- **{rm.model}** ({rm.pricing_band}) — {rm.rationale}")

    a("\n## Distribution & GTM Channels")
    for ch in r.gtm_channels:
        a(f"- {ch}")

    a("\n## Risks, Blockers & Compliance Concerns")
    for risk in r.risks:
        a(f"- _[{risk.type}/{risk.severity}]_ {risk.risk}")

    a(f"\n## Final Recommendation: **{r.recommendation.upper()}**")
    a(f"\n**Confidence:** {r.confidence}")

    a("\n## Sources")
    for src in r.sources:
        a(f"- [{src.title or src.url}]({src.url}) _({src.source_type})_")

    return "\n".join(out)
