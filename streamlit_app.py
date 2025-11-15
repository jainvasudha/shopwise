"""Streamlit interface for the ShopWise price comparison agent."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional
import hashlib
import json
import os
import re

import psycopg
from psycopg_pool import ConnectionPool
import streamlit as st

from src.price_agent.agent import ProductResult, collect_results
from src.price_agent.evaluator import evaluate_with_galileo
from src.price_agent.summarize import summarize_with_claude


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SPECIAL_CHARS = "!@#$%^&*()-_=+[]{};:'\",.<>/?`~|\\"
SIGNUP_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS signup_profiles (
    id BIGSERIAL PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    organization TEXT NOT NULL,
    major TEXT NOT NULL,
    university TEXT NOT NULL,
    location TEXT NOT NULL,
    purpose_choices JSONB NOT NULL DEFAULT '[]'::jsonb,
    purpose_text TEXT,
    terms_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    privacy_accepted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""


def init_session_state() -> None:
    """Ensure common session keys are initialized exactly once."""
    if "latest_results" not in st.session_state:
        st.session_state["latest_results"] = {"results": [], "summary": "", "raw_dicts": [], "query": ""}
    if "signup_records" not in st.session_state:
        st.session_state["signup_records"] = []
    if "signup_complete" not in st.session_state:
        st.session_state["signup_complete"] = False
    if "signup_defaults" not in st.session_state:
        st.session_state["signup_defaults"] = {}
    if "db_ready" not in st.session_state:
        st.session_state["db_ready"] = False
    if "db_error" not in st.session_state:
        st.session_state["db_error"] = ""


@st.cache_resource(show_spinner=False)
def get_db_pool() -> Optional[ConnectionPool]:
    """Create and cache a connection pool for Neon."""
    url = os.getenv("DATABASE_URL")
    if not url:
        return None
    return ConnectionPool(conninfo=url, min_size=1, max_size=4, kwargs={"autocommit": True})


def init_database() -> None:
    """Ensure the Neon table is ready before accepting submissions."""
    pool = get_db_pool()
    if not pool:
        st.session_state["db_ready"] = False
        st.session_state["db_error"] = "DATABASE_URL not set; Neon storage disabled."
        return

    try:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(SIGNUP_TABLE_SQL)
        st.session_state["db_ready"] = True
        st.session_state["db_error"] = ""
    except psycopg.Error as exc:
        st.session_state["db_ready"] = False
        st.session_state["db_error"] = f"Neon setup failed: {exc.pgerror or exc}"


def persist_signup_record(record: Dict[str, Any]) -> bool:
    """Insert the signup record into Neon if possible."""
    pool = get_db_pool()
    if not pool:
        return False

    try:
        with pool.connection() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO signup_profiles (
                    full_name, email, password_hash, organization,
                    major, university, location, purpose_choices,
                    purpose_text, terms_accepted, privacy_accepted
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
                """,
                (
                    record["full_name"],
                    record["email"],
                    record["password_hash"],
                    record["organization"],
                    record["major"],
                    record["university"],
                    record["location"],
                    json.dumps(record["purpose_choices"]),
                    record["purpose_text"],
                    record["terms"],
                    record["privacy"],
                ),
            )
        return True
    except psycopg.Error as exc:
        st.session_state["db_ready"] = False
        st.session_state["db_error"] = f"Failed to store signup: {exc.pgerror or exc}"
        return False


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


def password_feedback(password: str) -> Dict[str, bool]:
    """Return requirement checks used for inline password feedback."""
    return {
        "At least 8 characters": len(password) >= 8,
        "Contains a number": any(char.isdigit() for char in password),
        "Contains an uppercase letter": any(char.isupper() for char in password),
        "Contains a special character": any(char in SPECIAL_CHARS for char in password),
    }


def render_password_validation(password: str) -> None:
    """Display contextual password strength hints."""
    if not password:
        st.caption("Password must be at least 8 characters and include a mix of characters.")
        return

    checks = password_feedback(password)
    passed = sum(checks.values())
    strength = ["Weak", "Fair", "Good", "Strong"]
    st.progress(passed / len(checks))
    st.caption(f"Password strength: {strength[passed-1] if passed else strength[0]}")
    for label, ok in checks.items():
        icon = "✅" if ok else "⚠️"
        st.caption(f"{icon} {label}")


def hash_password(password: str) -> str:
    """Hash the password before storing in-memory."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def validate_signup_form(data: Dict[str, str], accepted_terms: bool, accepted_privacy: bool) -> List[str]:
    """Validate signup fields and return a list of error messages, if any."""
    errors: List[str] = []
    if not data["full_name"].strip():
        errors.append("Full name is required.")
    if not EMAIL_PATTERN.match(data["email"]):
        errors.append("Enter a valid email address.")
    password_checks = password_feedback(data["password"])
    if not all(password_checks.values()):
        errors.append("Password must meet all strength requirements.")
    if not data["organization"].strip():
        errors.append("Company / school / organization is required.")
    if not data["major"].strip():
        errors.append("Tell us your major or primary focus area.")
    if not data["university"].strip():
        errors.append("University or campus must be provided.")
    if not data["location"].strip():
        errors.append("Share your location so we can localize retailers.")
    if not data["purpose_choices"] and not data["purpose_text"].strip():
        errors.append("Share at least one purpose so we can tailor results.")
    if not accepted_terms or not accepted_privacy:
        errors.append("Please confirm that you agree to the privacy policy and terms.")
    return errors


def render_signup_form() -> bool:
    """Collect onboarding inputs before revealing the shopping experience."""
    st.header("Step 1 · Create your ShopWise profile")
    st.write(
        "We personalize pricing tips and sustainability insights based on your major, campus, goals, and organization."
    )
    if st.session_state.get("db_error"):
        st.warning(
            "Neon storage is currently unavailable. Submissions will be kept for this session only.\n\n"
            f"Details: {st.session_state['db_error']}"
        )

    defaults = st.session_state.get("signup_defaults", {})

    with st.form("signup_form", clear_on_submit=False):
        st.markdown("### Basic information")
        col1, col2 = st.columns(2)
        full_name = col1.text_input("Full name *", value=defaults.get("full_name", ""), placeholder="Taylor Rivera")
        email = col2.text_input(
            "Work or school email *",
            value=defaults.get("email", ""),
            placeholder="taylor@campus.edu",
            help="Used for confirmations and personalized deal alerts.",
        )

        org = st.text_input(
            "Company, school, or organization *",
            value=defaults.get("organization", ""),
            placeholder="Columbia University · Sustainability Lab",
        )

        password = st.text_input(
            "Create a password *",
            value=defaults.get("password", ""),
            placeholder="Use 8+ characters, mix letters/numbers/symbols",
            type="password",
        )
        render_password_validation(password)

        st.markdown("### Student profile")
        col3, col4, col5 = st.columns(3)
        major = col3.text_input(
            "Major or focus area *",
            value=defaults.get("major", ""),
            placeholder="Sustainable Design / Computer Science",
        )
        university = col4.text_input(
            "University / campus *",
            value=defaults.get("university", ""),
            placeholder="Columbia University",
            help="Used to unlock local student deals and bookstore pricing.",
        )
        location = col5.text_input(
            "Current location *",
            value=defaults.get("location", ""),
            placeholder="New York, NY",
        )

        purpose_choices = st.multiselect(
            "Primary reasons you're here *",
            options=[
                "Compare prices quickly",
                "Track sustainability / carbon impact",
                "Find exclusive student deals",
                "Equip classrooms or teams",
                "Other research",
            ],
            default=defaults.get("purpose_choices", []),
            help="Helps us prioritize what to show you first.",
        )
        purpose_text = st.text_area(
            "Anything else we should know? (optional)",
            value=defaults.get("purpose_text", ""),
            placeholder="e.g., Need energy-efficient monitors for new design lab.",
        )
        st.markdown("### Privacy & next steps")
        accepted_terms = st.checkbox(
            "I agree to the Terms of Service *",
            value=defaults.get("terms", False),
        )
        accepted_privacy = st.checkbox(
            "I agree to the Privacy Policy *",
            value=defaults.get("privacy", False),
        )

        submitted = st.form_submit_button("Save and continue to ShopWise")

    data = {
        "full_name": full_name,
        "email": email.strip(),
        "password": password,
        "organization": org,
        "major": major,
        "university": university,
        "location": location,
        "purpose_choices": purpose_choices,
        "purpose_text": purpose_text,
    }

    if submitted:
        errors = validate_signup_form(data, accepted_terms, accepted_privacy)
        st.session_state["signup_defaults"] = {**data, "terms": accepted_terms, "privacy": accepted_privacy}
        if errors:
            for err in errors:
                st.error(err)
            return False

        record = {
            **data,
            "password_hash": hash_password(password),
            "terms": accepted_terms,
            "privacy": accepted_privacy,
        }
        st.session_state["signup_records"].append(record)
        st.session_state["latest_signup"] = record
        st.session_state["signup_complete"] = True
        st.session_state["signup_defaults"]["password"] = ""
        stored = persist_signup_record(record)
        st.success(f"Thanks, {data['full_name'].split()[0]}! Your preferences are saved.")
        if stored:
            st.caption("Signup securely stored in Neon.")
        else:
            st.warning("Saved for this session only because Neon is unreachable right now.")
        st.info(
            "Next up: enter a product to compare student pricing, view carbon insights, and opt into Galileo reliability checks."
        )
        return True

    if st.session_state.get("signup_complete") and "latest_signup" in st.session_state:
        latest = st.session_state["latest_signup"]
        st.success(
            f"Welcome back, {latest['full_name']}! "
            "Your profile helps us highlight relevant stores, discounts, and sustainability callouts."
        )
        st.caption(f"{latest['major']} · {latest['university']} · {latest['location']}")
        st.caption(
            f"Focus area: {', '.join(latest['purpose_choices']) or latest['purpose_text'] or 'General exploration'}"
        )
        return True

    st.info("Complete the quick signup above to unlock tailored ShopWise recommendations.")
    return False


def main() -> None:
    """Render the Streamlit UI and drive user interactions."""
    st.set_page_config(page_title="ShopWise", page_icon="🛒", layout="wide")
    st.title("ShopWise – Student-Friendly Sustainable Shopping")
    st.write(
        "Use ShopWise to explore **budget-friendly** and **lower-carbon** picks across trusted retailers. "
        "Start by telling us a bit about you so recommendations stay relevant."
    )

    st.markdown(
        "1. Complete the signup so we can align pricing tips with your major and campus.\n"
        "2. Enter the product you need once the form is approved.\n"
        "3. Adjust listing depth, sort by price or carbon, and review AI summaries.\n"
        "4. Tap **Buy Now** or expand **More Info** for deeper details.\n"
        "5. Optional: run Galileo reliability checks for extra assurance."
    )

    init_session_state()
    init_database()

    signup_ready = render_signup_form()

    if not signup_ready:
        return

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

