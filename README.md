# ShopWise

ShopWise is a student-focused shopping assistant that compares prices across major retailers (Amazon, Walmart, Best Buy, Newegg), surfaces affordable picks for any product category, estimates a carbon footprint score, and summarizes the best deals using Claude.

## Prerequisites

- Python 3.11+
- Recommended: virtual environment (`python -m venv .venv` and `source .venv/bin/activate`)
- API keys
  - `ANTHROPIC_API_KEY` for Claude summaries
  - Optional `GALILEO_API_KEY` (and `GALILEO_ENDPOINT`) for reliability checks

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Streamlit App

1. Export your credentials inside the terminal (or add them to `~/.zshrc`):
   ```bash
   export ANTHROPIC_API_KEY="your-claude-key"
   export GALILEO_API_KEY="your-galileo-key"   # optional
   # export GALILEO_ENDPOINT="https://..."     # optional override
   ```
2. Launch the UI from your Daytona workspace (or any terminal):
   ```bash
   streamlit run streamlit_app.py
   ```
3. Open the provided local/remote URL in your browser.
4. Enter any product (e.g., “wireless headphones”, “graphing calculator”, “laptop”), use the slider to adjust how many listings per store you want, then:
   - Sort results by **Lowest Price** or **Lowest Carbon Footprint** using the toggle buttons.
   - Review each interactive card (price badge, carbon icon, quick “Buy Now” button, and “More Info” expander).
   - Read Claude’s highlighted recommendation panel and optionally run the Galileo reliability check with one click.

> **Note:** Some retailers occasionally rate-limit automated traffic with HTTP 503 responses. The app now retries requests and falls back to other stores automatically, but if a store repeatedly fails you can rerun the search after a short pause.

## Legacy CLI (optional)

You can still run the CLI for quick smoke tests:

```bash
python main.py --query "wireless headphones" --limit 3
```

The CLI prints the ranked list, summary, and Galileo evaluation to stdout. Use this for debugging or scripted runs if you prefer terminal output.*** End Patch

