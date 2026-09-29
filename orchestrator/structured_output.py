import json
import re
from datetime import datetime, timezone


class ModelRateLimitError(RuntimeError):
    """Raised when the configured model provider has no remaining quota."""


def raise_if_rate_limited(exc: Exception) -> None:
    text = str(exc)
    if "RateLimitError" not in type(exc).__name__ and "Error code: 429" not in text and "'code': 429" not in text:
        return
    reset_match = re.search(r"X-RateLimit-Reset['\"\s:]+(\d{10,13})", text, re.IGNORECASE)
    reset_text = "the provider's next daily reset"
    if reset_match:
        timestamp = int(reset_match.group(1))
        if timestamp > 10_000_000_000:
            timestamp /= 1000
        reset_text = datetime.fromtimestamp(timestamp, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    raise ModelRateLimitError(
        "The configured OpenRouter free-model quota is exhausted. "
        f"Wait until {reset_text}, add OpenRouter credits, or configure another provider in Settings."
    ) from exc


def extract_json_object(content) -> dict:
    """Extract one JSON object from common model response shapes."""
    if isinstance(content, list):
        content = "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    text = str(content or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else text
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("Model returned no JSON object")
        value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("Structured response must be a JSON object")
    return value
