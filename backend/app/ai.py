import json
import re
from .config import settings

SYSTEM = """Extract travel enquiry details. Return only JSON with keys destination, travel_month, nights, adults, children, total_budget_inr, must_haves, confidence, draft_reply. Use null for unknown values. confidence is an object mapping each extracted field to a number 0..1. Do not invent package prices. Keep draft_reply concise and do not promise availability."""


def _local_fallback(message: str) -> dict:
    """Conservative local parser for demos/offline use; every field remains unverified."""
    text = message.lower()
    adults_match = re.search(r"(\d+)\s+adults?", text)
    children_match = re.search(r"(\d+)\s+(?:kids?|children)", text)
    nights_match = re.search(r"(\d+)\s*(?:-|to)\s*(\d+)\s+nights?|(\d+)\s+nights?", text)
    budget_match = re.search(r"(?:budget(?:\s+around)?\s*|₹\s*|rs\.?\s*)(\d+(?:\.\d+)?)\s*(lakh|lac|lakhs|k)?", text)
    budget = None
    if budget_match:
        amount = float(budget_match.group(1))
        unit = (budget_match.group(2) or "").strip()
        multiplier = 100000 if unit in {"lakh", "lac", "lakhs"} else 1000 if unit == "k" else 1
        budget = int(amount * multiplier)
    month = next((m.title() for m in ("january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december") if m in text), None)
    destination = next((d for d in ("Kerala", "Munnar", "Thekkady", "Alleppey", "Tamil Nadu", "Madurai", "Rameswaram", "Kanyakumari") if d.lower() in text), None)
    must_haves = [item for item in ("houseboat", "wildlife", "tea gardens", "beach", "temple") if item in text]
    nights = int(nights_match.group(1) or nights_match.group(3)) if nights_match else None
    return {
        "destination": destination,
        "travel_month": month,
        "nights": nights,
        "nights_range": [int(nights_match.group(1)), int(nights_match.group(2))] if nights_match and nights_match.group(2) else ([nights] if nights is not None else None),
        "adults": int(adults_match.group(1)) if adults_match else None,
        "children": int(children_match.group(1)) if children_match else None,
        "total_budget_inr": budget,
        "must_haves": must_haves,
        "confidence": {"destination": 0.55, "travel_month": 0.55, "nights": 0.5, "travellers": 0.5, "budget": 0.4},
        "draft_reply": "Thank you for sharing your travel plans. Our team will review the dates, group size and preferences, then confirm suitable options and current pricing.",
        "needs_manual_review": True,
        "provider": "local_fallback",
    }


def extract_enquiry(message: str) -> dict:
    if not settings.openai_api_key:
        return _local_fallback(message)
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key, timeout=20.0, max_retries=1)
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": message}],
    )
    data = json.loads(response.choices[0].message.content or "{}")
    confidence = data.get("confidence") or {}
    data["needs_manual_review"] = any(float(v) < 0.75 for v in confidence.values()) if confidence else True
    data["provider"] = "openai_api"
    return data
