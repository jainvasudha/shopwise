"""Interface to Galileo for safety/reliability checks with graceful fallback."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

import requests

GALILEO_ENDPOINT = os.getenv("GALILEO_ENDPOINT", "https://api.galileo.ai/v1/evaluate")


def evaluate_with_galileo(payload: Dict) -> Dict:
    api_key = os.getenv("GALILEO_API_KEY")
    if not api_key:
        return {"status": "skipped", "reason": "Missing GALILEO_API_KEY"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            GALILEO_ENDPOINT,
            headers=headers,
            data=json.dumps(payload),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:  # pragma: no cover - network dependency
        return {"status": "error", "reason": str(exc)}

