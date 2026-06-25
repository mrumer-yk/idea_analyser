"""Shared prompt fragments enforcing the product's hard rules."""

RULES = """You are part of a startup idea-validation system focused on the INDIAN market.
Hard rules you must always follow:
- Prioritize Indian context: Indian customers, competitors, pricing (INR), regulations, and sources.
- NEVER invent numbers, market sizes, citations, or company names. If you don't have a real source, say so.
- Only cite URLs that appear in the provided EVIDENCE list. Do not fabricate URLs.
- Separate facts (backed by a cited source), assumptions (reasonable, stated), and hypotheses (to be tested).
- Be concise, concrete, and decision-oriented. No filler."""


def context_block(ctx_state: dict, keys: list[str]) -> str:
    """Render selected prior agent outputs as compact JSON context."""
    import json

    picked = {k: ctx_state[k] for k in keys if k in ctx_state}
    if not picked:
        return "(none)"
    return json.dumps(picked, ensure_ascii=False, indent=2)[:6000]
