"""Claude-powered summarization with graceful fallback."""

from __future__ import annotations

import os
from typing import List, Optional

try:
    from anthropic import Anthropic
except ImportError:  # pragma: no cover - optional dependency
    Anthropic = None  # type: ignore


def summarize_with_claude(query: str, ranked_results: List[dict]) -> str:
    if not ranked_results:
        return "I could not find any listings to summarize."

    api_key = os.getenv("ANTHROPIC_API_KEY")
    bullet_lines = []
    for item in ranked_results:
        carbon = item.get("carbon", {})
        carbon_label = carbon.get("label", "Unknown impact")
        carbon_kg = carbon.get("kg_co2e", "?")
        bullet_lines.append(
            f"- {item['store']} {item['name']} at ${item['price']:.2f}, "
            f"ethical score {item['ethical_score']}, carbon {carbon_label} (~{carbon_kg} kg CO2e)"
        )
    default_summary = (
        f"Top findings for '{query}':\n" + "\n".join(bullet_lines) + "\n"
        "Pick the best balance of price and sustainability for your needs."
    )

    if not api_key or Anthropic is None:
        return default_summary

    client = Anthropic(api_key=api_key)
    prompt = (
        "You are advising a cost-conscious yet sustainability-minded student. "
        "Summarize the best purchase options based on price and ethical score. "
        "Highlight the cheapest and the most sustainable picks. "
        "If helpful, include suggestions for trade-offs.\n\n"
        f"Query: {query}\n"
        "Ranked Options:\n"
        + "\n".join(bullet_lines)
    )

    try:
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=200,
            temperature=0.5,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].get("text") if response.content else None
        return content or default_summary
    except Exception:  # pragma: no cover - network dependency
        return default_summary

