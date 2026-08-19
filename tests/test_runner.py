"""Tests for runner module."""
import pytest
from unittest.mock import Mock, patch
from src.runner import run_model_test
from src.models import ModelResult
from src.retry import RetryConfig


def test_test_model_success():
    """Test successful model test."""
    # Mock successful response
    mock_response = {
        'id': 'test-id',
        'choices': [{'message': {'content': 'Test response'}}]
    }
    
    with patch('src.runner.request_json') as mock_request:
        mock_request.return_value = (mock_response, 200, '{"test": "response"}')
        
        result = run_model_test(
            completions_url="http://test.com/v1/chat/completions",
            api_key="test-key",
            model="test-model",
            max_tokens=25,
            session=Mock(),
            timeout=30,
            verbose=False,
            run_label="01/01",
            max_model_len=20,
            enable_retry=False
        )
        
        assert result.ok is True
        assert result.model == "test-model"
        assert result.status_code == 200
        assert result.error is None


def test_test_model_http_error():
    """Test model test with HTTP error."""
    from src.models import HttpStatusError
    
    with patch('src.runner.request_json') as mock_request:
        mock_request.side_effect = HttpStatusError(500, "Server Error", None)
        
        result = run_model_test(
            completions_url="http://test.com/v1/chat/completions",
            api_key="test-key",
            model="test-model",
            max_tokens=25,
            session=Mock(),
            timeout=30,
            verbose=False,
            run_label="01/01",
            max_model_len=20,
            enable_retry=False
        )
        
        assert result.ok is False
        assert result.status_code == 500
        assert "http_error" in result.error


def test_test_model_empty_response():
    """Test model test with empty response content."""
    mock_response = {
        'id': 'test-id',
        'choices': [{'message': {'content': ''}}]
    }
    
    with patch('src.runner.request_json') as mock_request:
        mock_request.return_value = (mock_response, 200, '{}')
        
        result = run_model_test(
            completions_url="http://test.com/v1/chat/completions",
            api_key="test-key",
            model="test-model",
            max_tokens=25,
            session=Mock(),
            timeout=30,
            verbose=False,
            run_label="01/01",
            max_model_len=20,
            enable_retry=False
        )
        
        assert result.ok is False
        assert result.error == "no_text_in_response"


def test_test_model_with_retry():
    """Test model test with retry enabled."""
    mock_response = {
        'id': 'test-id',
        'choices': [{'message': {'content': 'Success after retry'}}]
    }
    
    retry_config = RetryConfig(max_attempts=2, initial_delay=0.1)
    
    with patch('src.runner.request_json') as mock_request:
        mock_request.return_value = (mock_response, 200, '{"test": "response"}')
        
        result = run_model_test(
            completions_url="http://test.com/v1/chat/completions",
            api_key="test-key",
            model="test-model",
            max_tokens=25,
            session=Mock(),
            timeout=30,
            verbose=False,
            run_label="01/01",
            max_model_len=20,
            enable_retry=True,
            retry_config=retry_config
        )
        
        assert result.ok is True
