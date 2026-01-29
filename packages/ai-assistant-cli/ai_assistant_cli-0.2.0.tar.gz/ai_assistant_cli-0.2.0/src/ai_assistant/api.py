import json
import requests

# Global variable to store API key at runtime
_api_key = None

API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
)


def set_api_key(key: str):
    """Set the API key to be used by call_ai."""
    global _api_key
    _api_key = key


def call_ai(prompt: str) -> str:
    """Call the Google Gemini API with the given prompt."""
    if not _api_key:
        return "API key not configured"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(
            f"{API_URL}?key={_api_key}",
            headers={"Content-Type": "application/json"},
            data= json.dumps(payload),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]

    except requests.exceptions.HTTPError as e:
        return f"HTTP error: {e.response.status_code} - {e.response.text}"
    except requests.exceptions.RequestException as e:
        return f"Request failed: {str(e)}"
    except (KeyError, IndexError):
        return "Unexpected response format from API"
