"""Shared Gemini API client configuration."""

import json
import re

import httpx

GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)


def parse_json_response(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None


def generate_json(
    api_key: str,
    prompt: str,
    image_bytes: bytes | None = None,
    mime_type: str = "image/jpeg",
    timeout: float = 45.0,
    temperature: float = 0.05,
) -> dict | None:
    parts: list[dict] = [{"text": prompt}]
    if image_bytes:
        import base64
        parts.append({
            "inline_data": {
                "mime_type": mime_type,
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }
        })

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json",
        },
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(GEMINI_URL, params={"key": api_key}, json=payload)
        resp.raise_for_status()
        data = resp.json()

    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    return parse_json_response(text)
