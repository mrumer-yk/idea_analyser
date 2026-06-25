"""Pydantic models for the final report JSON contract.

The synthesizer's output is validated against ``Report`` before persistence so
the API always returns a stable shape to the frontend.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Classification = Literal["fact", "assumption", "hypothesis"]
Recommendation = Literal["pursue", "pivot", "reject"]
Confidence = Literal["low", "medium", "high"]


def _normalize(value, mapping: dict, default: str) -> str:
    """Coerce free-form model output to an allowed enum value.

    Agents occasionally emit synonyms ('medium' for 'med', 'legal' for
    'compliance'). Rather than let one stray value fail the whole Report and
    blank the entire analysis, we map known variants and fall back safely.
    """
    if isinstance(value, str):
        key = value.strip().lower()
        if key in mapping:
            return mapping[key]
    return default


class FitFactor(BaseModel):
    name: str
    weight: float = 0.0
    score: float = 0.0


class IndiaMarketFit(BaseModel):
    score: float = 0.0  # 0..10
    rationale: str = ""
    factors: list[FitFactor] = Field(default_factory=list)


class Segment(BaseModel):
    segment: str
    persona: str = ""
    pains: list[str] = Field(default_factory=list)
    jtbd: list[str] = Field(default_factory=list)


class Competitor(BaseModel):
    name: str
    type: Literal["direct", "indirect"] = "direct"
    positioning: str = ""
    pricing: str = ""
    url: str = ""

    @field_validator("type", mode="before")
    @classmethod
    def _norm(cls, v):
        if isinstance(v, str) and "indirect" in v.strip().lower():
            return "indirect"
        return "direct"


class MarketSignal(BaseModel):
    claim: str
    classification: Classification = "hypothesis"
    source_url: Optional[str] = None

    @field_validator("classification", mode="before")
    @classmethod
    def _norm(cls, v):
        return _normalize(v, {
            "fact": "fact", "facts": "fact", "factual": "fact",
            "assumption": "assumption", "assumptions": "assumption", "assumed": "assumption",
            "hypothesis": "hypothesis", "hypotheses": "hypothesis", "hypothetical": "hypothesis",
        }, "hypothesis")


class MarketSize(BaseModel):
    tam: Optional[str] = None
    sam: Optional[str] = None
    som: Optional[str] = None
    assumptions: list[str] = Field(default_factory=list)
    grounded: bool = False


class RevenueModel(BaseModel):
    model: str
    pricing_band: str = ""
    rationale: str = ""


class Risk(BaseModel):
    risk: str
    type: Literal["market", "execution", "compliance"] = "market"
    severity: Literal["low", "med", "high"] = "med"

    @field_validator("type", mode="before")
    @classmethod
    def _norm_type(cls, v):
        return _normalize(v, {
            "market": "market", "demand": "market", "competition": "market", "financial": "market",
            "execution": "execution", "operational": "execution", "technical": "execution",
            "product": "execution", "team": "execution",
            "compliance": "compliance", "legal": "compliance", "regulatory": "compliance",
            "privacy": "compliance", "security": "compliance",
        }, "market")

    @field_validator("severity", mode="before")
    @classmethod
    def _norm_sev(cls, v):
        return _normalize(v, {
            "low": "low", "minor": "low",
            "med": "med", "medium": "med", "moderate": "med", "mid": "med",
            "high": "high", "critical": "high", "severe": "high", "major": "high",
        }, "med")


class Source(BaseModel):
    title: str = ""
    url: str
    source_type: str = "other"


class Report(BaseModel):
    idea_summary: str = ""
    problem_and_pain: str = ""
    india_market_fit: IndiaMarketFit = Field(default_factory=IndiaMarketFit)
    target_segments: list[Segment] = Field(default_factory=list)
    competitors: list[Competitor] = Field(default_factory=list)
    market_signals: list[MarketSignal] = Field(default_factory=list)
    market_size: MarketSize = Field(default_factory=MarketSize)
    revenue_models: list[RevenueModel] = Field(default_factory=list)
    gtm_channels: list[str] = Field(default_factory=list)
    risks: list[Risk] = Field(default_factory=list)
    recommendation: Recommendation = "pivot"
    confidence: Confidence = "low"
    sources: list[Source] = Field(default_factory=list)

    @field_validator("recommendation", mode="before")
    @classmethod
    def _norm_rec(cls, v):
        return _normalize(v, {
            "pursue": "pursue", "go": "pursue", "build": "pursue", "proceed": "pursue", "yes": "pursue",
            "pivot": "pivot", "explore": "pivot", "maybe": "pivot", "iterate": "pivot",
            "reject": "reject", "kill": "reject", "stop": "reject", "no": "reject", "pass": "reject",
        }, "pivot")

    @field_validator("confidence", mode="before")
    @classmethod
    def _norm_conf(cls, v):
        return _normalize(v, {
            "low": "low",
            "medium": "medium", "med": "medium", "moderate": "medium",
            "high": "high",
        }, "low")
