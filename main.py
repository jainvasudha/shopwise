"""CLI entrypoint for the ShopWise price comparison agent."""

from __future__ import annotations

import argparse
from typing import Iterable

from src.price_agent.agent import run_agent


def format_result(rank: int, item) -> str:
    return (
        f"{rank}. ${item.price:.2f} – {item.store}\n"
        f"   Name: {item.name}\n"
        f"   Ethical Score: {item.ethical_score}/5\n"
        f"   Link: {item.link}\n"
    )


def prompt_for_query() -> str:
    try:
        return input("Enter a product to search for: ").strip()
    except EOFError:
        return ""


def main() -> None:
    parser = argparse.ArgumentParser(description="Find the lowest priced sustainable option.")
    parser.add_argument("--query", help="Product name to search for")
    parser.add_argument("--limit", type=int, default=5, help="Listings per store to fetch")
    args = parser.parse_args()

    query = args.query.strip() if args.query else prompt_for_query()
    if not query:
        raise SystemExit("No search query provided.")

    agent_output = run_agent(query, limit_per_store=args.limit)
    ranked_results = agent_output["results"]

    print(f"Search: \"{query}\"\n")

    if not ranked_results:
        print("No listings found. Please try another item or check your network connection.")
    else:
        for idx, result in enumerate(ranked_results, start=1):
            print(format_result(idx, result))

    print("Summary:")
    print(agent_output["summary"])
    print("\nGalileo evaluation:")
    print(agent_output["evaluation"])


if __name__ == "__main__":
    main()

