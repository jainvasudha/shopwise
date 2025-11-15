"""Simple sustainability/ethical scoring utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .scrapers import RawListing

BASE_STORE_SCORES: Dict[str, int] = {
    "Amazon": 2,
    "Walmart": 3,
    "Best Buy": 3,
    "Newegg": 2,
}

KEYWORD_BONUSES: Dict[str, int] = {
    "refurbished": 1,
    "renewed": 1,
    "eco": 2,
    "recycled": 2,
    "organic": 2,
    "fair trade": 2,
    "solar": 1,
    "energy star": 1,
}


def score_listing(listing: RawListing) -> int:
    base_score = BASE_STORE_SCORES.get(listing.store, 2)
    name_lower = listing.name.lower()
    bonus = sum(points for keyword, points in KEYWORD_BONUSES.items() if keyword in name_lower)
    score = max(1, min(5, base_score + bonus))
    return score

