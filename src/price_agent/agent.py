"""Core agent logic for fetching, scoring, and summarizing product listings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List

from .carbon import CarbonEstimate, estimate_carbon
from .evaluator import evaluate_with_galileo
from .scoring import score_listing
from .scrapers import fetch_all
from .summarize import summarize_with_claude


@dataclass
class ProductResult:
    store: str
    name: str
    price: float
    link: str
    ethical_score: int
    carbon: CarbonEstimate


def collect_results(query: str, limit_per_store: int = 5) -> List[ProductResult]:
    raw_listings = fetch_all(query, limit_per_store=limit_per_store)
    results: List[ProductResult] = []
    seen_links: set[str] = set()

    for listing in raw_listings:
        if listing.link in seen_links:
            continue
        seen_links.add(listing.link)
        score = score_listing(listing)
        carbon_estimate = estimate_carbon(listing)
        results.append(
            ProductResult(
                store=listing.store,
                name=listing.name,
                price=listing.price,
                link=listing.link,
                ethical_score=score,
                carbon=carbon_estimate,
            )
        )

    return sorted(results, key=lambda item: (item.price, -item.ethical_score))


def run_agent(query: str, limit_per_store: int = 5) -> Dict:
    ranked_results = collect_results(query, limit_per_store=limit_per_store)
    summary = summarize_with_claude(query, [asdict(item) for item in ranked_results])

    galileo_payload = {
        "task": "price_comparison",
        "query": query,
        "results": [asdict(item) for item in ranked_results],
        "summary": summary,
    }
    evaluation = evaluate_with_galileo(galileo_payload)

    return {
        "query": query,
        "results": ranked_results,
        "summary": summary,
        "evaluation": evaluation,
    }

