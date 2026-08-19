"""Tests for response validation."""
from src.validation import extract_text, validate_response_text


def test_extract_text_from_openai_format():
    """Test extracting text from OpenAI format."""
    response = {
        'choices': [{
            'message': {
                'content': 'Hello, world!'
            }
        }]
    }
    
    text = extract_text(response)
    assert text == 'Hello, world!'


def test_extract_text_from_legacy_format():
    """Test extracting text from legacy completion format."""
    response = {
        'choices': [{
            'text': 'Hello, world!'
        }]
    }
    
    text = extract_text(response)
    assert text == 'Hello, world!'


def test_extract_text_from_streaming_format():
    """Test extracting text from streaming delta format."""
    response = {
        'choices': [{
            'delta': {
                'content': 'Hello, world!'
            }
        }]
    }
    
    text = extract_text(response)
    assert text == 'Hello, world!'


def test_extract_text_returns_none_for_empty():
    """Test that None is returned for responses without text."""
    assert extract_text({}) is None
    assert extract_text({'choices': []}) is None
    assert extract_text({'choices': [{}]}) is None


def test_validate_response_text_accepts_valid():
    """Test validation accepts non-empty text."""
    ok, error = validate_response_text("Hello, world!")
    assert ok is True
    assert error is None


def test_validate_response_text_rejects_empty():
    """Test validation rejects empty text."""
    ok, error = validate_response_text("")
    assert ok is False
    assert error == "empty_response"
    
    ok, error = validate_response_text("   ")
    assert ok is False
    assert error == "empty_response"
