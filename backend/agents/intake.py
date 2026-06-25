"""Agent 1 — Intake / Extractor.

Normalizes the raw input into a core idea + business hypothesis. If the input
is a URL, the page is fetched first and product positioning/pricing/ICP/claims
are extracted. Also proposes India-biased search queries for the researcher.
"""
from __future__ import annotations

from .base import Agent
from .context import Evidence, RunContext
from .prompts import RULES

SYSTEM = RULES + """

Your role: INTAKE ANALYST. Extract the core idea and business hypothesis."""

USER_TMPL = """Raw input ({input_type}):
\"\"\"
{raw}
\"\"\"

{url_block}

Return a JSON object with exactly these keys:
{{
  "core_idea": "one-paragraph plain-English description of the idea",
  "business_hypothesis": "the central bet (who, problem, why now)",
  "product_signals": {{
     "positioning": "", "features": [], "pricing": "", "icp": "", "proof": [], "claims": []
  }},
  "assumptions": ["explicit assumptions you are making"],
  "search_queries": ["6-10 India-focused web search queries to validate this idea, covering competitors, pricing, market reports, regulation, and demand signals"],
  "market_size_queries": ["3-5 search queries that name the BROADER or ADJACENT India markets whose published market size could anchor a TAM, e.g. 'India conversational AI market size 2024', 'India contact center software market size USD billion', 'India sales automation market revenue forecast'"]
}}
If the input is not a URL, fill product_signals from the text where possible (leave blanks otherwise)."""


class IntakeAgent(Agent):
    name = "intake"

    async def run(self, ctx: RunContext) -> dict:
        await ctx.emit(self.name, "started", "Extracting core idea", None)

        url_block = ""
        if ctx.input_type == "url" and ctx.source_url:
            await ctx.emit(self.name, "info", f"Fetching {ctx.source_url}", None)
            page = await ctx.fetcher.fetch(ctx.source_url)
            if page.ok and page.text:
                ctx.add_evidence(
                    [Evidence(title=page.title or ctx.source_url, url=ctx.source_url,
                              snippet=page.text[:500], source_type="other")]
                )
                from ..security import wrap_untrusted

                url_block = (
                    f"Fetched page title: {page.title}\nPage content:\n"
                    f"{wrap_untrusted(page.text[:6000])}"
                )
            else:
                url_block = f"(could not fetch the URL: {page.error})"

        user = USER_TMPL.format(
            input_type=ctx.input_type,
            raw=(ctx.raw_input or ctx.source_url or "")[:4000],
            url_block=url_block,
        )
        result = await self.complete_json(ctx, SYSTEM, user)
        ctx.state["intake"] = result
        await ctx.emit(
            self.name, "finished", "Idea extracted",
            {"queries": result.get("search_queries", [])},
        )
        return result
