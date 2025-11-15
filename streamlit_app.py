"""Streamlit interface for the ShopWise price comparison agent."""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List

import streamlit as st

from src.price_agent.agent import ProductResult, collect_results
from src.price_agent.evaluator import evaluate_with_galileo
from src.price_agent.summarize import summarize_with_claude


def run_search_flow(query: str, limit: int) -> Dict[str, List]:
    """Fetch listings, score them, and summarize via Claude."""
    results = collect_results(query, limit_per_store=limit)
    result_dicts = [asdict(item) for item in results]
    summary = summarize_with_claude(query, result_dicts)
    return {"results": results, "summary": summary, "raw_dicts": result_dicts}


def sort_results(results: List[ProductResult], mode: str) -> List[ProductResult]:
    """Sort results based on the selected mode (price or carbon)."""
    if mode == "Lowest Carbon Footprint":
        return sorted(results, key=lambda item: (item.carbon.kg_co2e, item.price))
    return sorted(results, key=lambda item: (item.price, item.carbon.kg_co2e))


def carbon_badge(result: ProductResult) -> str:
    """Return a color-coded badge string representing the carbon footprint."""
    label = result.carbon.label
    icon = "🌿" if label == "Low impact" else "🌎" if label == "Moderate impact" else "🔥"
    color = ":green" if label == "Low impact" else ":orange" if label == "Moderate impact" else ":red"
    return f"{icon} {color}[{label}] (~{result.carbon.kg_co2e} kg CO₂e)"


def render_result_cards(results: List[ProductResult]) -> None:
    """Render each result as an interactive card with expandable details."""
    if not results:
        st.info("No listings found yet. Try searching for another product.")
        return

    st.subheader("Top Student-Friendly Picks")
    for idx, result in enumerate(results, start=1):
        with st.container(border=True):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"### {result.name}")
                st.caption(f"Store: {result.store}")
                st.write(f"💸 **Student Price:** ${result.price:.2f}")
                st.write(carbon_badge(result))
            with col2:
                st.link_button("Buy Now", url=result.link, use_container_width=True)

            with st.expander("More Info"):
                st.write(f"- Ethical score: {result.ethical_score}/5")
                st.write(f"- Carbon estimate: ~{result.carbon.kg_co2e} kg CO₂e")
                st.write(
                    "These estimates help weigh affordability against sustainability for student budgets."
                )


def render_summary(summary: str) -> None:
    """Render Claude's narrative summary."""
    st.subheader("Claude's Recommendation")
    with st.container(border=True):
        st.write("🤖 **AI Summary for Students**")
        st.markdown(summary)


def render_galileo_section(query: str, raw_dicts: List[Dict]) -> None:
    """Optionally send the structured results to Galileo for reliability feedback."""
    if not raw_dicts:
        return

    st.subheader("Need extra assurance?")
    run_eval = st.button("Run Galileo Reliability Check", use_container_width=True)
    if run_eval:
        with st.spinner("Contacting Galileo..."):
            payload = {
                "task": "price_comparison",
                "query": query,
                "results": raw_dicts,
                "summary": summarize_with_claude(query, raw_dicts),
            }
            st.session_state["galileo"] = evaluate_with_galileo(payload)

    if "galileo" in st.session_state:
        st.json(st.session_state["galileo"])


def main() -> None:
    """Render the Streamlit UI and drive user interactions."""
    st.set_page_config(page_title="ShopWise", page_icon="🛒", layout="wide")
    st.title("ShopWise – Student-Friendly Sustainable Shopping")
    st.write(
        "Use ShopWise to explore **budget-friendly** and **lower-carbon** picks across trusted retailers. "
        "Input any product (laptops, headphones, books, dorm gear, etc.), then compare options instantly."
    )

    st.markdown(
        "1. Enter the product you need.\n"
        "2. Adjust the per-store listing count if you want more results.\n"
        "3. Sort by price or carbon footprint using the controls.\n"
        "4. Tap **Buy Now** or expand **More Info** for deeper details.\n"
        "5. Review Claude's AI guidance to pick the smartest option."
    )

    if "latest_results" not in st.session_state:
        st.session_state["latest_results"] = {"results": [], "summary": "", "raw_dicts": [], "query": ""}

    with st.form("search_form"):
        product_query = st.text_input(
            "What are you shopping for?",
            value=st.session_state["latest_results"]["query"],
            placeholder="e.g. wireless headphones, graphing calculator, eco backpack",
        )
        limit = st.slider("Listings per store", min_value=1, max_value=5, value=3)
        submitted = st.form_submit_button("Find the best student options")

    if submitted:
        if not product_query.strip():
            st.warning("Please enter a product name before searching.")
        else:
            with st.spinner("Gathering listings..."):
                data = run_search_flow(product_query.strip(), limit)
            st.session_state["latest_results"] = {
                "results": data["results"],
                "summary": data["summary"],
                "raw_dicts": data["raw_dicts"],
                "query": product_query.strip(),
            }

    state = st.session_state["latest_results"]

    if state["results"]:
        sort_mode = st.radio(
            "Sort results by",
            options=["Lowest Price", "Lowest Carbon Footprint"],
            horizontal=True,
        )
        sorted_results = sort_results(state["results"], sort_mode)
        render_result_cards(sorted_results)
        render_summary(state["summary"])
        render_galileo_section(state["query"], state["raw_dicts"])
    else:
        st.info("Search for something like 'wireless headphones' to get started.")


if __name__ == "__main__":
    main()

