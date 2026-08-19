import json
from typing import Any, Dict, Optional, Tuple


def get_finish_reason(response: Dict[str, Any]) -> Optional[str]:
    if not isinstance(response, dict):
        return None

    if "choices" in response and response["choices"]:
        choice = response["choices"][0]

        return choice.get("finish_reason") or choice.get("native_finish_reason")

    return None


def extract_text(response: Dict[str, Any]) -> Optional[str]:
    """Extract text from various API response formats.
    
    Supports:
    - OpenAI format: choices[0].message.content
    - Legacy completion: choices[0].text
    - Anthropic format: output[].content[].text
    - Delta format (streaming): choices[0].delta.content
    """
    if not isinstance(response, dict):
        return None

    # OpenAI chat completion format
    if "choices" in response and response["choices"]:
        choice = response["choices"][0]

        # Standard message format
        if "message" in choice and isinstance(choice["message"], dict):
            content = choice["message"].get("content")
            if content:
                return content
        
        # Streaming delta format
        if "delta" in choice and isinstance(choice["delta"], dict):
            content = choice["delta"].get("content")
            if content:
                return content

        # Legacy text completion format
        if "text" in choice:
            text = choice.get("text")
            if text:
                return text

    # Anthropic format
    if "output" in response and isinstance(response["output"], list):
        for item in response["output"]:
            if isinstance(item, dict):
                content = item.get("content")

                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "output_text":
                            text = block.get("text")
                            if text:
                                return text
    
    # Direct text field (some providers)
    if "text" in response:
        text = response.get("text")
        if text:
            return text
    
    # Content field directly (some providers)
    if "content" in response:
        content = response.get("content")
        if isinstance(content, str) and content:
            return content

    return None


def strip_markdown_fences(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.split("\n", 1)

        if len(lines) > 1:
            text = lines[1]

        else:
            text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return text.strip()


def validate_response_text(text: str) -> Tuple[bool, Optional[str]]:
    """Validate response text from API.
    
    Args:
        text: Response text from the model
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "empty_response"

    return True, None
