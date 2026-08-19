"""Tests for configuration management."""
from src.config import normalize_base_url, build_completions_url


def test_normalize_base_url_removes_trailing_slash():
    """Test that trailing slashes are removed."""
    assert normalize_base_url("http://localhost:8000/") == "http://localhost:8000"
    assert normalize_base_url("http://localhost:8000///") == "http://localhost:8000"


def test_normalize_base_url_keeps_url_without_slash():
    """Test that URLs without trailing slash are unchanged."""
    assert normalize_base_url("http://localhost:8000") == "http://localhost:8000"


def test_build_completions_url_avoids_double_v1():
    """Test that double /v1/v1 paths are avoided."""
    # Base URL with /v1, endpoint with /v1
    url = build_completions_url("http://localhost:8000/v1", "/v1/chat/completions")
    assert url == "http://localhost:8000/v1/chat/completions"
    assert "/v1/v1" not in url
    
    # Base URL without /v1, endpoint with /v1
    url = build_completions_url("http://localhost:8000", "/v1/chat/completions")
    assert url == "http://localhost:8000/v1/chat/completions"
    
    # Base URL with /v1, endpoint without /v1
    url = build_completions_url("http://localhost:8000/v1", "/chat/completions")
    assert url == "http://localhost:8000/v1/chat/completions"


def test_build_completions_url_adds_leading_slash():
    """Test that endpoints without leading slash get one added."""
    url = build_completions_url("http://localhost:8000", "chat/completions")
    assert url == "http://localhost:8000/chat/completions"
