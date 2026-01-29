import json
import requests
from .config import API_KEY

API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
)


def call_ai(prompt: str) -> str:
    if not API_KEY:
        return "API key not configured"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    response = requests.post(
        f"{API_URL}?key={API_KEY}",
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=30
    )

    response.raise_for_status()
    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]
