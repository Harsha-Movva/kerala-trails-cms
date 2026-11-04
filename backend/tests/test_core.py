from app.ai import extract_enquiry
from app.seed import PACKAGES

def test_seed_contains_client_sample_packages():
    codes = {p["code"] for p in PACKAGES}
    assert {"PKG-KL-07", "PKG-SI-12"}.issubset(codes)
    kerala = next(p for p in PACKAGES if p["code"] == "PKG-KL-07")
    assert [s["price_per_person"] for s in kerala["seasons"]] == [32500, 24900]

def test_ai_without_provider_marks_for_manual_review(monkeypatch):
    from app import ai
    monkeypatch.setattr(ai.settings, "openai_api_key", None)
    result = extract_enquiry("2 adults and 1 kid, Kerala in December")
    assert result["needs_manual_review"] is True
    assert result["provider"] == "local_fallback"
    assert "draft_reply" in result


def test_local_fallback_extracts_sample_enquiry_without_claiming_certainty(monkeypatch):
    from app import ai
    monkeypatch.setattr(ai.settings, "openai_api_key", None)
    result = extract_enquiry("Hi, 2 adults and 1 kid, Kerala 5-6 nights in December, budget around 1.2 lakh total, houseboat a must")
    assert result["destination"] == "Kerala"
    assert result["travel_month"] == "December"
    assert result["nights"] == 5
    assert result["nights_range"] == [5, 6]
    assert result["adults"] == 2
    assert result["children"] == 1
    assert result["total_budget_inr"] == 120000
    assert "houseboat" in result["must_haves"]
    assert result["needs_manual_review"] is True
