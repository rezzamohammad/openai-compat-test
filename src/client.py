from typing import Any, Dict, List, Optional, Tuple
import requests
import sys
from .config import normalize_base_url
from .models import HttpStatusError
from .response_parser import ResponseParser


PROMPT_TEMPLATE = """Generate a unique and creative response that is approximately {max_tokens} tokens in length.

Return a JSON object with the strict structure:

{{
  "status": "OK",
  "content": "[Insert Response Here]"
}}

Rules:
- The response MUST be valid JSON
- Do NOT include any extra keys
- Do NOT include markdown
- The content must be creative and coherent"""

AUDIT_PROMPT = '''
You are being audited.

Keep the answer under {max_tokens} tokens.

Return ONLY valid JSON with this exact schema:
{{
  "claims": {{
    "model_name": null,
    "provider_name": null,
    "knows_with_certainty": false,
    "evidence": "text"
  }}
}}
'''

def request_json(
    session: requests.Session,
    url: str,
    method: str,
    headers: Dict[str, str],
    payload: Optional[Dict[str, Any]],
    timeout: int,
) -> Tuple[Dict[str, Any], int, str]:
    kwargs: Dict[str, Any] = {"headers": headers, "timeout": timeout, "stream": True}

    if payload is not None:
        kwargs["json"] = payload

    resp = session.request(method, url, **kwargs)

    # Check if this is a chat completion endpoint
    is_chat_endpoint = '/chat/completions' in url

    if is_chat_endpoint:
        # Use ResponseParser for chat completions (handles SSE, JSON, etc)
        parser = ResponseParser(resp)
        data = parser.parse()
        text = getattr(parser, '_cached_text', '[Stream - not cacheable]')

        # If parsing failed, try to get error message
        if not data:
            error_msg = parser.get_error_message()
            data = {"error": {"message": error_msg}} if error_msg else {}
    else:
        # For non-chat endpoints (like /models), just parse as JSON
        text = resp.text
        try:
            data = resp.json()
        except:
            data = {}

    if resp.status_code >= 400:
        raise HttpStatusError(resp.status_code, text[:2000] if text else "", data or None)

    return data, resp.status_code, text


def get_models_url(base_url: str) -> str:
    base_url = normalize_base_url(base_url)
    if base_url.endswith("/v1"):
        return f"{base_url}/models"
    return f"{base_url}/v1/models"


def fetch_models(base_url: str, api_key: str, session: requests.Session, timeout: int) -> List[str]:
    url = get_models_url(base_url)
    headers = {"Authorization": f"Bearer {api_key}"}
    data, _, _ = request_json(session, url, "GET", headers, None, timeout)
    items = data.get("data", [])
    models = []

    for item in items:
        model_id = item.get("id")

        if model_id:
            models.append(model_id)

    return models


def build_chat_payload(model: str, max_tokens: int, stream: bool = False) -> Dict[str, Any]:
    prompt = AUDIT_PROMPT.format(max_tokens=max_tokens)

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.8,
    }

    # Add stream parameter if explicitly set
    if stream:
        payload["stream"] = True

    return payload
