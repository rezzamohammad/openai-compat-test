"""Tests for response parser."""
import json
from unittest.mock import Mock
from src.response_parser import ResponseParser


def test_parse_standard_json():
    """Test parsing standard OpenAI JSON response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.json.return_value = {
        'id': 'test-123',
        'model': 'cx/gpt-5.5-xhigh',
        'choices': [{
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': 'Hello, world!'
            },
            'finish_reason': 'stop'
        }]
    }

    parser = ResponseParser(mock_response)
    result = parser.parse()

    assert result['id'] == 'test-123'
    assert result['model'] == 'cx/gpt-5.5-xhigh'
    assert result['choices'][0]['message']['content'] == 'Hello, world!'


def test_parse_sse_stream():
    """Test parsing SSE stream response."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/event-stream'}

    # Simulate SSE stream
    sse_lines = [
        'data: {"id":"chat-1","model":"cx/gpt-5.5-xhigh","choices":[{"index":0,"delta":{"content":"Hello"}}]}',
        'data: {"id":"chat-1","choices":[{"index":0,"delta":{"content":" world"}}]}',
        'data: {"id":"chat-1","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}',
        'data: [DONE]'
    ]
    mock_response.iter_lines.return_value = sse_lines

    parser = ResponseParser(mock_response)
    result = parser.parse()

    assert result['id'] == 'chat-1'
    assert result['model'] == 'cx/gpt-5.5-xhigh'
    assert result['choices'][0]['message']['content'] == 'Hello world'
    assert result['choices'][0]['finish_reason'] == 'stop'


def test_parse_error_response():
    """Test parsing error response."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.headers = {'Content-Type': 'application/json'}
    mock_response.json.return_value = {
        'error': {
            'message': 'Invalid API key',
            'type': 'invalid_request_error'
        }
    }

    parser = ResponseParser(mock_response)
    result = parser.parse()

    assert 'error' in result
    assert result['error']['message'] == 'Invalid API key'


def test_get_error_message():
    """Test error message extraction."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {
        'error': {
            'message': 'Internal server error'
        }
    }

    parser = ResponseParser(mock_response)
    error_msg = parser.get_error_message()

    assert error_msg == 'Internal server error'
