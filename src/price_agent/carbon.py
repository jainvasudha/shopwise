"""Estimate a coarse carbon footprint score for each listing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .scrapers import RawListing


@dataclass
class CarbonEstimate:
    """Represents a simple carbon estimate in kg CO2e plus a readability label."""

    kg_co2e: float
    label: str


# Baseline kg CO2e estimates per product category sourced from public LCA writeups.
CARBON_CATEGORY_BASE: Dict[str, float] = {
    "laptop": 200.0,
    "notebook": 5.0,
    "headphone": 45.0,
    "earbud": 30.0,
    "phone": 120.0,
    "tablet": 110.0,
    "calculator": 15.0,
    "mouse": 25.0,
    "keyboard": 35.0,
    "backpack": 40.0,
    "book": 8.0,
    "textbook": 18.0,
    "charger": 10.0,
    "monitor": 140.0,
}

LOWER_IMPACT_KEYWORDS = {"refurbished", "renewed", "recycled", "eco", "sustainable"}
HIGHER_IMPACT_KEYWORDS = {"gaming", "4k", "ultra", "pro"}


def _infer_category(name: str) -> str:
    lowered = name.lower()
    for keyword in CARBON_CATEGORY_BASE:
        if keyword in lowered:
            return keyword
    return "generic"


def estimate_carbon(listing: RawListing) -> CarbonEstimate:
    """Return an approximate carbon footprint for a product listing."""

    category = _infer_category(listing.name)
    base = CARBON_CATEGORY_BASE.get(category, 80.0)

    lowered = listing.name.lower()
    if any(word in lowered for word in LOWER_IMPACT_KEYWORDS):
        base *= 0.8
    if any(word in lowered for word in HIGHER_IMPACT_KEYWORDS):
        base *= 1.15

    # Small adjustment for price (cheaper often means lighter/simpler devices).
    if listing.price < 50:
        base *= 0.9
    elif listing.price > 500:
        base *= 1.1

    if base <= 30:
        label = "Low impact"
    elif base <= 120:
        label = "Moderate impact"
    else:
        label = "High impact"

    return CarbonEstimate(kg_co2e=round(base, 1), label=label)

