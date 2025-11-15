"""FastAPI server exposing the ShopWise price comparison API.

This wraps the existing Python backend logic (scrapers, scoring, carbon,
summarization, Galileo evaluation) behind HTTP endpoints that a separate
TypeScript/React frontend can call.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.price_agent.agent import ProductResult, collect_results
from src.price_agent.evaluator import evaluate_with_galileo
from src.price_agent.summarize import summarize_with_claude


app = FastAPI(title="ShopWise API", version="0.1.0")


# --- CORS configuration -----------------------------------------------------

# Allow localhost for local dev, and Daytona workspace URLs
# Daytona typically forwards ports with URLs like: https://<workspace-id>-<port>.app.daytona.io
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",  # typical React dev server
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https?://.*\.app\.daytona\.io",  # Daytona workspace URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Pydantic models --------------------------------------------------------


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Product search query")
    limit: int = Field(
        3,
        ge=1,
        le=10,
        description="Number of listings per store to fetch",
    )


class CarbonResponse(BaseModel):
    kg_co2e: float
    label: str


class ProductResponse(BaseModel):
    store: str
    name: str
    price: float
    link: str
    ethical_score: int
    carbon: CarbonResponse


class SearchResponse(BaseModel):
    query: str
    results: List[ProductResponse]
    summary: str


# --- Helpers ----------------------------------------------------------------


def _product_to_response(result: ProductResult) -> ProductResponse:
    """Convert internal ProductResult dataclass to API response model."""
    return ProductResponse(
        store=result.store,
        name=result.name,
        price=result.price,
        link=result.link,
        ethical_score=result.ethical_score,
        carbon=CarbonResponse(
            kg_co2e=result.carbon.kg_co2e,
            label=result.carbon.label,
        ),
    )


# --- Routes -----------------------------------------------------------------


@app.get("/api/health", tags=["meta"])
def health_check() -> Dict[str, str]:
    """Simple health check."""
    return {"status": "ok"}


@app.post("/api/search", response_model=SearchResponse, tags=["search"])
def search_products(payload: SearchRequest) -> SearchResponse:
    """Main search endpoint.

    This mirrors the behavior of `run_search_flow` / `run_agent` used in the
    Streamlit and CLI entrypoints, but returns structured JSON for a JS client.
    """
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    try:
        results = collect_results(query, limit_per_store=payload.limit)
        result_dicts = [asdict(item) for item in results]
        summary = summarize_with_claude(query, result_dicts)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SearchResponse(
        query=query,
        results=[_product_to_response(r) for r in results],
        summary=summary,
    )


@app.post("/api/evaluate", tags=["evaluation"])
def evaluate(payload: Dict) -> Dict:
    """Forward a payload to Galileo for optional reliability checks."""
    try:
        return evaluate_with_galileo(payload)
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


