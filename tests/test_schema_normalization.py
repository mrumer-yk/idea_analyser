"""Enum normalization keeps one stray agent value from blanking the report."""
from backend.schemas import Report


def test_synonyms_are_normalized_not_fatal():
    report = Report.model_validate({
        "idea_summary": "x",
        "competitors": [{"name": "Foo", "type": "Indirect competitor"}],
        "market_signals": [{"claim": "y", "classification": "Facts"}],
        "risks": [
            {"risk": "a", "type": "legal", "severity": "medium"},   # was the crash
            {"risk": "b", "type": "regulatory", "severity": "critical"},
        ],
        "recommendation": "GO",
        "confidence": "moderate",
    })
    # Nothing raised; values coerced to allowed enums.
    assert report.competitors[0].type == "indirect"
    assert report.market_signals[0].classification == "fact"
    assert report.risks[0].severity == "med"
    assert report.risks[0].type == "compliance"
    assert report.risks[1].severity == "high"
    assert report.recommendation == "pursue"
    assert report.confidence == "medium"
    # The rest of the report survived intact.
    assert report.idea_summary == "x"


def test_unknown_values_fall_back_safely():
    report = Report.model_validate({
        "risks": [{"risk": "a", "type": "weird", "severity": "spicy"}],
        "recommendation": "???",
    })
    assert report.risks[0].type == "market"
    assert report.risks[0].severity == "med"
    assert report.recommendation == "pivot"
