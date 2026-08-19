"""Tests for client module."""
import pytest
from src.client import build_chat_payload, get_models_url


def test_build_chat_payload_basic():
    """Test basic chat payload construction."""
    payload = build_chat_payload("test-model", 50, stream=False)
    
    assert payload["model"] == "test-model"
    assert payload["max_tokens"] == 50
    assert payload["temperature"] == 0.8
    assert "messages" in payload
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"
    assert "stream" not in payload


def test_build_chat_payload_with_streaming():
    """Test chat payload with streaming enabled."""
    payload = build_chat_payload("test-model", 100, stream=True)
    
    assert payload["model"] == "test-model"
    assert payload["stream"] is True


def test_get_models_url_with_v1():
    """Test models URL construction with /v1 in base URL."""
    url = get_models_url("http://localhost:8000/v1")
    assert url == "http://localhost:8000/v1/models"


def test_get_models_url_without_v1():
    """Test models URL construction without /v1 in base URL."""
    url = get_models_url("http://localhost:8000")
    assert url == "http://localhost:8000/v1/models"


def test_get_models_url_with_trailing_slash():
    """Test models URL construction with trailing slash."""
    url = get_models_url("http://localhost:8000/v1/")
    assert url == "http://localhost:8000/v1/models"
