"""Agent 5 — Market Sizing (TAM/SAM/SOM).

Default behavior is to PRODUCE a transparent top-down estimate built on a real,
cited anchor figure from the evidence (e.g. a broader market size) plus
explicitly stated share/adoption assumptions. The anchor must come from
evidence (never invented); the share %s are assumptions, clearly labeled.
Only when NO quantitative anchor exists at all do we return nulls.
"""
from __future__ import annotations

import asyncio

from .base import Agent, render_evidence
from .context import Evidence, RunContext
from .prompts import RULES, context_block
from .researcher import _classify_source

SYSTEM = RULES + """

Your role: MARKET SIZING analyst. Your DEFAULT is to deliver a usable India
TAM/SAM/SOM estimate, not to refuse. Use the standard top-down method:
- Find the best ANCHOR figure in the evidence. The anchor MUST be a stated
  TOTAL-MARKET revenue/size for a BROADER or ADJACENT India market (e.g. "India
  conversational-AI market valued at INR X Bn", "India contact-center market
  USD Y Mn, CAGR Z%"). The anchor must be a real number FROM the evidence —
  never invent it.
- A per-customer PRICE, per-minute rate, or per-month plan (e.g. "₹15,000/month",
  "₹10/min") is NOT a market size and MUST NOT be used as the anchor. If the
  evidence contains only such prices and NO total-market figure, return nulls
  with grounded=false — do not turn a price into a TAM.
- TAM = the anchor (or a clearly-reasoned narrowing of it).
- SAM = TAM x a STATED serviceable-share % (state the % and the reason).
- SOM = SAM x a STATED obtainable-share % over a stated horizon (e.g. 3 yrs).
Show the arithmetic.

IMPORTANT — what is ALLOWED and expected:
- Applying a clearly-stated serviceable-share % to an adjacent/broader market
  anchor IS an accepted estimation method. It is NOT fabrication.
- You do NOT need a bottom-up count of firms or a per-account spend benchmark.
  Do not refuse just because an exact India SMB count is missing — use the
  top-down anchor instead.
- Label the anchor as a cited fact and every % as a labeled assumption.

Worked example of the expected output style (illustrative only — use the real
anchor from THIS evidence):
  ANCHOR: India conversational-AI market = INR 38.1 Bn (2024) [<source url>]
  TAM = INR 38.1 Bn ; SAM = 25% serviceable (voice/sales-call slice) = INR 9.5 Bn ;
  SOM = 5% obtainable over 3 yrs = INR 0.48 Bn.

Only return nulls + grounded=false if there is NO market-revenue figure for ANY
broader or adjacent India market anywhere in the evidence."""

USER_TMPL = """Idea + research + segments:
{ctx}

MARKET-SIZE EVIDENCE (search these FIRST for a total-market anchor figure; cite these URLs):
{anchors}

OTHER EVIDENCE (cite only these URLs):
{evidence}

Return JSON:
{{
  "market_size": {{
    "tam": "INR value with unit, e.g. 'INR 38.10 Bn (2024)' — or null only if no anchor exists",
    "sam": "INR value derived from TAM x serviceable-share %",
    "som": "INR value derived from SAM x obtainable-share % over the horizon",
    "assumptions": [
      "ANCHOR: <figure> from <source URL in EVIDENCE>",
      "TAM = <reasoning/arithmetic>",
      "SAM = TAM x <share %> because <reason>",
      "SOM = SAM x <%> over <N> years because <reason>"
    ],
    "grounded": true|false
  }}
}}
Prefer to estimate. grounded=true when the estimate rests on a cited anchor plus
the stated assumptions. Return nulls + grounded=false ONLY when no quantitative
anchor exists anywhere in the evidence (and explain that in assumptions)."""


class SizingAgent(Agent):
    name = "sizing"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Estimating TAM/SAM/SOM", None)

        # Actively pull market-size anchors into the cited evidence pool before
        # estimating, so the model has a real figure to build a top-down estimate.
        anchors = await self._gather_market_size_anchors(ctx)

        user = USER_TMPL.format(
            ctx=context_block(ctx.state, ["intake", "research", "segmentation"]),
            anchors=self._render_anchors(anchors),
            evidence=render_evidence(ctx),
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["sizing"] = result
        ms = result.get("market_size", {})
        await ctx.emit(
            self.name, "finished",
            f"Sizing grounded={ms.get('grounded')}", None,
        )
        return result

    async def _gather_market_size_anchors(self, ctx: RunContext) -> list[Evidence]:
        """Run targeted searches for India market-size figures and cite them.

        Returns the newly-added evidence so the caller can show it to the model
        as a dedicated block (the general evidence render is capped and would
        otherwise truncate these freshly-appended anchors out)."""
        from ..security import sanitize_external_text

        intake = ctx.state.get("intake", {}) or {}
        # Prefer the adjacent-market queries the intake agent proposed (it knows
        # the category); fall back to topic-derived queries.
        queries = [q for q in (intake.get("market_size_queries") or []) if isinstance(q, str)][:5]
        if not queries:
            topic = (intake.get("core_idea") or ctx.raw_input or "").strip()[:80]
            if not topic:
                return []
            queries = [
                f"{topic} market size India 2024 billion",
                f"India {topic} market size revenue forecast crore",
            ]

        async def _do(q: str):
            try:
                return await ctx.search.search(q, max_results=4)
            except Exception:
                return []

        batches = await asyncio.gather(*[_do(q) for q in queries])
        before = len(ctx.evidence)
        for results in batches:
            ctx.add_evidence(
                [
                    Evidence(
                        title=r.title, url=r.url,
                        snippet=sanitize_external_text(r.snippet),
                        source_type=_classify_source(r.url),
                    )
                    for r in results
                ]
            )
        added = ctx.evidence[before:]

        # Deepen the top new results so the anchor figure lands in the snippet.
        for e in added[:4]:
            if len(e.snippet or "") < 300:
                page = await ctx.fetcher.fetch(e.url)
                if page.ok and page.text:
                    e.snippet = sanitize_external_text(page.text[:1000])

        await ctx.emit(
            self.name, "info", f"+{len(added)} market-size sources", {"added": len(added)}
        )
        return added

    @staticmethod
    def _render_anchors(anchors: list[Evidence]) -> str:
        if not anchors:
            return "(no dedicated market-size sources found)"
        lines = []
        for e in anchors[:15]:
            snippet = (e.snippet or "").replace("\n", " ")[:600]
            lines.append(f"- {e.title} | {e.url}\n  {snippet}")
        return "\n".join(lines)
