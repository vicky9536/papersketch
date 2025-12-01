# src/papersketch/client.py

import httpx
from config import PAPERSKETCH_ENDPOINT, PAPERSKETCH_API_KEY, REQUEST_TIMEOUT


class PaperSketchClient:
    """Thin wrapper around the Papersketch HTTP API."""

    def __init__(self) -> None:
        if not PAPERSKETCH_API_KEY:
            raise RuntimeError(
                "PAPERSKETCH_API_KEY is not set. "
                "Add it to your .env file in the project root."
            )

    def summarize(self, url: str, lang: str = "en") -> dict:
        try:
            resp = httpx.get(
                PAPERSKETCH_ENDPOINT,
                params={"url": url, "lang": lang},
                headers={"X-API-Key": PAPERSKETCH_API_KEY},
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.ReadTimeout:
            raise RuntimeError("PaperSketch request timed out; try again or use an uploaded PDF.")
