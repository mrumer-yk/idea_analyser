import pytest

from backend.agents.context import RunContext
from backend.agents.orchestrator import run_pipeline
from backend.config import Settings
from backend.schemas import Report

from .fakes import FakeFetcher, FakeLLM, FakeSearch, URL_PRICING


def _ctx() -> RunContext:
    return RunContext(
        run_id="t1",
        input_type="text",
        raw_input="A UPI-first expense tracker for Indian freelancers.",
        source_url=None,
        llm=FakeLLM(),
        search=FakeSearch(),
        fetcher=FakeFetcher(),
        settings=Settings(),
    )


async def test_pipeline_produces_full_report():
    out = await run_pipeline(_ctx())
    report: Report = out["report"]

    # All required sections present and typed.
    assert report.idea_summary
    assert report.problem_and_pain
    assert report.india_market_fit.score == 6.5
    assert len(report.target_segments) == 1
    assert report.recommendation in {"pursue", "pivot", "reject"}
    assert report.confidence in {"low", "medium", "high"}

    # Every market signal is classified.
    assert report.market_signals
    for sig in report.market_signals:
        assert sig.classification in {"fact", "assumption", "hypothesis"}

    # Competitor enrichment filled intel fields.
    razor_c = [c for c in report.competitors if c.name == "Razorpay"]
    assert razor_c and razor_c[0].funding and razor_c[0].founded == "2014"
    assert razor_c[0].weakness

    # Cross-validator tagged signals and corroborated the verified one.
    razor = [s for s in report.market_signals if "Razorpay" in s.claim]
    assert razor and razor[0].verification == "verified"
    assert razor[0].corroborating_url  # independent second source

    # New agents populate their sections.
    assert len(report.demand_signals) == 2
    assert report.demand_signals[0].sentiment in {"pain", "desire", "objection", "neutral"}
    assert len(report.pivots) == 2
    assert report.pivots[0].direction

    # Markdown renders.
    assert "# India Market Validation Report" in out["report_md"]
    assert "Final Recommendation" in out["report_md"]
    assert "Demand Signals" in out["report_md"]
    assert "Pivot Options" in out["report_md"]


async def test_pipeline_enforces_evidence_discipline():
    out = await run_pipeline(_ctx())
    report: Report = out["report"]
    violations = out["violations"]

    # The fabricated-URL numeric "fact" must have been downgraded + uncited.
    fabricated = [s for s in report.market_signals if "15 million" in s.claim]
    assert fabricated, "expected the freelancer-count signal"
    assert fabricated[0].classification == "hypothesis"  # downgraded
    assert fabricated[0].source_url is None  # unseen URL stripped

    # Competitor citing an unseen URL had its url blanked.
    ghost = [c for c in report.competitors if c.name == "Ghostco"]
    assert ghost and ghost[0].url == ""

    # Razorpay's real (searched) URL survives.
    razor = [c for c in report.competitors if c.name == "Razorpay"]
    assert razor and razor[0].url == URL_PRICING

    # Sources only contain retrieved evidence URLs.
    src_urls = {s.url for s in report.sources}
    assert URL_PRICING in src_urls
    assert "https://fabricated.example.com/made-up" not in src_urls
    assert violations  # fixes were recorded
