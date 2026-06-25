"""In-memory fakes for testing the pipeline without network/LLM calls."""
from __future__ import annotations

import json

from backend.llm.base import LLMResponse
from backend.research.base import SearchResult
from backend.research.fetcher import FetchedPage

URL_PRICING = "https://razorpay.com/pricing/"
URL_NEWS = "https://inc42.com/report"


def _by_role(system: str) -> dict:
    if "INTAKE ANALYST" in system:
        return {
            "core_idea": "A UPI-first expense tracker for Indian freelancers.",
            "business_hypothesis": "Freelancers in India will pay for automated GST-ready bookkeeping.",
            "product_signals": {"positioning": "", "features": [], "pricing": "",
                                 "icp": "freelancers", "proof": [], "claims": []},
            "assumptions": ["Freelancers file GST"],
            "search_queries": ["expense tracker india pricing", "freelancer bookkeeping india"],
        }
    if "MARKET RESEARCHER" in system:
        return {
            "findings": [
                {"claim": "Razorpay charges 2% per transaction", "classification": "fact",
                 "source_url": URL_PRICING},
                {"claim": "India has 15 million freelancers", "classification": "fact",
                 "source_url": "https://fabricated.example.com/made-up"},
                {"claim": "Demand is likely rising post-2020", "classification": "hypothesis",
                 "source_url": None},
            ],
            "summary": "There is competition but room in the GST niche.",
        }
    if "COMPETITOR ANALYST" in system:
        return {
            "competitors": [
                {"name": "Razorpay", "type": "indirect", "positioning": "payments",
                 "pricing": "2%", "url": URL_PRICING},
                {"name": "Ghostco", "type": "direct", "positioning": "x",
                 "pricing": "", "url": "https://ghost.example.com/unseen"},
            ],
            "gaps": ["No GST-native freelancer tool"],
        }
    if "CUSTOMER SEGMENTATION" in system:
        return {"segments": [{"segment": "Freelancers", "persona": "Riya, designer",
                              "pains": ["manual GST"], "jtbd": ["file taxes"]}]}
    if "MARKET SIZING" in system:
        return {"market_size": {"tam": "₹500 Cr", "sam": "₹120 Cr", "som": "₹12 Cr",
                                "assumptions": ["15M freelancers x ₹X"], "grounded": True}}
    if "MONETIZATION" in system:
        return {"revenue_models": [{"model": "SaaS subscription", "pricing_band": "₹199-499/mo",
                                    "rationale": "matches Indian SaaS norms"}],
                "gtm_channels": ["Instagram", "CA partnerships"]}
    if "INDIA-MARKET-FIT SCORER" in system:
        return {"india_market_fit": {"score": 6.5, "rationale": "moderate fit",
                "factors": [{"name": "willingness_to_pay", "weight": 0.3, "score": 6}]}}
    if "RED-TEAM CRITIC" in system:
        return {"weaknesses": ["low WTP"], "missing_evidence": ["actual freelancer count"],
                "risks": [{"risk": "DPDP compliance", "type": "compliance", "severity": "high"}]}
    if "SENIOR PRODUCT STRATEGIST" in system:
        return {"idea_summary": "UPI expense tracker for freelancers.",
                "problem_and_pain": "Manual GST bookkeeping is painful.",
                "recommendation": "pursue", "confidence": "medium"}
    return {}


class FakeLLM:
    name = "fake"

    async def complete(self, system, user, *, json_mode=False, max_tokens=4096, temperature=0.3):
        return LLMResponse(text=json.dumps(_by_role(system)), input_tokens=100, output_tokens=50)


class FakeSearch:
    name = "fake-search"

    async def search(self, query, *, max_results=5, include_domains=None):
        return [
            SearchResult(title="Razorpay Pricing", url=URL_PRICING, snippet="2% per transaction"),
            SearchResult(title="Inc42 Report", url=URL_NEWS, snippet="freelancer economy growing"),
        ]


class FakeFetcher:
    async def fetch(self, url):
        return FetchedPage(url=url, title="Fetched", text="some page content about " + url, ok=True)
