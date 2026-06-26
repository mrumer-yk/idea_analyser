"""Evidence-discipline guards: enforce "no invented numbers/citations".

These run on the synthesized report before persistence. Rather than fail the
whole run, we *sanitize* violations (downgrade unsupported numeric "facts" to
hypotheses, drop citations that point to URLs we never retrieved) and return a
list of violation messages for the audit trail.
"""
from __future__ import annotations

import re

from .schemas import Report

_NUMBER_RE = re.compile(r"\d")


def _has_number(text: str) -> bool:
    return bool(_NUMBER_RE.search(text or ""))


def enforce_evidence_discipline(
    report: Report, evidence_urls: set[str]
) -> tuple[Report, list[str]]:
    """Return a sanitized report and the list of violations found."""
    violations: list[str] = []

    # 1. market_signals: a numeric claim labeled 'fact' must cite a retrieved URL.
    for sig in report.market_signals:
        cited = sig.source_url in evidence_urls if sig.source_url else False
        if sig.source_url and not cited:
            violations.append(f"signal cites unseen URL: {sig.source_url!r}")
            sig.source_url = None
        if sig.classification == "fact" and _has_number(sig.claim) and not cited:
            violations.append(
                f"numeric claim labeled 'fact' without retrieved source -> "
                f"downgraded to hypothesis: {sig.claim[:80]!r}"
            )
            sig.classification = "hypothesis"

    # 1b. demand_signals: drop citations to URLs we never retrieved.
    for sig in report.demand_signals:
        if sig.source_url and sig.source_url not in evidence_urls:
            violations.append(f"demand signal cites unseen URL: {sig.source_url!r}")
            sig.source_url = None

    # 2. market_size: if it carries numbers it must be flagged grounded with
    #    stated assumptions; otherwise mark not grounded.
    ms = report.market_size
    size_text = " ".join(filter(None, [ms.tam, ms.sam, ms.som]))
    if _has_number(size_text) and not ms.assumptions:
        violations.append("market_size has numbers but no stated assumptions")
        ms.grounded = False

    # 3. sources: drop any source URL we never actually retrieved.
    kept = []
    for src in report.sources:
        if src.url in evidence_urls:
            kept.append(src)
        else:
            violations.append(f"dropped source not in evidence pool: {src.url!r}")
    report.sources = kept

    # 4. competitors: a cited competitor URL must be real; blank it if not.
    for comp in report.competitors:
        if comp.url and comp.url not in evidence_urls:
            violations.append(f"competitor cites unseen URL: {comp.url!r}")
            comp.url = ""

    return report, violations
