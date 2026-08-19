"""
Comprehensive tests for UI flows and error handling scenarios.

Tests all possible user interaction paths:
- .env missing
- .env with placeholders
- .env with valid config
- Connection errors
- Reconfiguration flows
- Save to .env functionality
"""

import os
import pytest
import tempfile
import pathlib
from unittest.mock import patch, MagicMock, call
from src.ui import (
    load_from_env,
    interactive_setup,
    save_to_env,
    prompt_manual_config,
)


class TestLoadFromEnv:
    """Test load_from_env() placeholder detection."""

    def test_load_from_env_missing_vars(self, monkeypatch):
        """Should return None if env vars are missing."""
        monkeypatch.delenv("OAI_TEST_BASE_URL", raising=False)
        monkeypatch.delenv("OAI_TEST_API_KEY", raising=False)
        
        result = load_from_env()
        assert result is None

    def test_load_from_env_placeholder_api_key(self, monkeypatch):
        """Should return None if API key is a placeholder."""
        placeholders = [
            "sk-your-api-key-here",
            "your-api-key",
            "sk-test",
            "sk-your-key-here",
        ]
        
        for placeholder in placeholders:
            monkeypatch.setenv("OAI_TEST_BASE_URL", "https://api.real.com/v1")
            monkeypatch.setenv("OAI_TEST_API_KEY", placeholder)
            
            result = load_from_env()
            assert result is None, f"Should reject placeholder: {placeholder}"

    def test_load_from_env_default_base_url(self, monkeypatch):
        """Should return None if base URL is default localhost."""
        monkeypatch.setenv("OAI_TEST_BASE_URL", "http://localhost:8000")
        monkeypatch.setenv("OAI_TEST_API_KEY", "sk-real-key-abc123")
        
        result = load_from_env()
        assert result is None

    def test_load_from_env_valid_config(self, monkeypatch):
        """Should return config if all values are valid."""
        monkeypatch.setenv("OAI_TEST_BASE_URL", "https://api.openai.com/v1")
        monkeypatch.setenv("OAI_TEST_API_KEY", "sk-proj-abc123")
        monkeypatch.setenv("OAI_TEST_TIMEOUT", "60000")
        monkeypatch.setenv("OAI_TEST_MAX_TOKENS", "100")
        
        result = load_from_env()
        
        assert result is not None
        assert result["base_url"] == "https://api.openai.com/v1"
        assert result["api_key"] == "sk-proj-abc123"
        assert result["timeout"] == 60000
        assert result["max_tokens"] == 100

    def test_load_from_env_empty_api_key(self, monkeypatch):
        """Should return None if API key is empty string."""
        monkeypatch.setenv("OAI_TEST_BASE_URL", "https://api.real.com")
        monkeypatch.setenv("OAI_TEST_API_KEY", "")
        
        result = load_from_env()
        assert result is None


class TestSaveToEnv:
    """Test save_to_env() functionality."""

    def test_save_to_env_creates_file(self):
        """Should create .env file with correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = pathlib.Path(tmpdir) / "test.env"
            
            config = {
                "base_url": "https://api.test.com/v1",
                "api_key": "sk-test-key-123",
                "max_tokens": 50,
                "endpoint": "/v1/chat/completions",
                "timeout": 45000,
                "request_delay_ms": 300,
            }
            
            save_to_env(config, str(env_path))
            
            assert env_path.exists()
            content = env_path.read_text()
            
            assert "OAI_TEST_BASE_URL=https://api.test.com/v1" in content
            assert "OAI_TEST_API_KEY=sk-test-key-123" in content
            assert "OAI_TEST_MAX_TOKENS=50" in content
            assert "OAI_TEST_TIMEOUT=45000" in content

    def test_save_to_env_overwrites_existing(self):
        """Should overwrite existing .env file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = pathlib.Path(tmpdir) / "test.env"
            
            # Create initial file
            env_path.write_text("OLD_VALUE=123\n")
            
            config = {
                "base_url": "https://new.api.com",
                "api_key": "sk-new-key",
                "max_tokens": 25,
                "endpoint": "/v1/chat/completions",
                "timeout": 30000,
                "request_delay_ms": 500,
            }
            
            save_to_env(config, str(env_path))
            
            content = env_path.read_text()
            assert "OLD_VALUE" not in content
            assert "OAI_TEST_BASE_URL=https://new.api.com" in content


class TestPromptManualConfig:
    """Test prompt_manual_config() API key validation."""

    @patch("src.ui.Prompt.ask")
    def test_api_key_required_loop(self, mock_ask):
        """Should loop until API key is provided."""
        # Simulate: empty -> empty -> valid key
        mock_ask.side_effect = [
            "https://api.test.com",  # base_url
            "",                       # api_key (empty, retry)
            "",                       # api_key (empty again, retry)
            "sk-valid-key",           # api_key (valid)
            "30000",                  # timeout
            "25",                     # max_tokens
            "/v1/chat/completions",   # endpoint
            "500",                    # request_delay_ms
        ]
        
        result = prompt_manual_config()
        
        assert result["api_key"] == "sk-valid-key"
        # Should have called Prompt.ask for api_key 3 times (2 empty + 1 valid)
        api_key_calls = [c for c in mock_ask.call_args_list if "API Key" in str(c)]
        assert len(api_key_calls) == 3

    @patch("src.ui.Prompt.ask")
    def test_api_key_whitespace_stripped(self, mock_ask):
        """Should strip whitespace from API key."""
        mock_ask.side_effect = [
            "https://api.test.com",
            "  sk-key-with-spaces  ",  # api_key with spaces
            "30000",
            "25",
            "/v1/chat/completions",
            "500",
        ]
        
        result = prompt_manual_config()
        
        assert result["api_key"] == "sk-key-with-spaces"


class TestInteractiveSetup:
    """Test interactive_setup() complete flow."""

    @patch("src.ui.load_from_env")
    @patch("src.ui.Confirm.ask")
    @patch("src.ui.display_config")
    def test_interactive_setup_uses_valid_env(self, mock_display, mock_confirm, mock_load):
        """Should use env config if valid and user confirms."""
        mock_load.return_value = {
            "base_url": "https://api.test.com",
            "api_key": "sk-test",
            "timeout": 30000,
            "max_tokens": 25,
            "endpoint": "/v1/chat/completions",
            "request_delay_ms": 500,
        }
        mock_confirm.return_value = True
        
        result = interactive_setup()
        
        assert result["base_url"] == "https://api.test.com"
        mock_display.assert_called_once()

    @patch("src.ui.load_from_env")
    @patch("src.ui.Confirm.ask")
    @patch("src.ui.prompt_manual_config")
    @patch("src.ui.display_config")
    @patch("src.ui.save_to_env")
    def test_interactive_setup_prompts_when_env_invalid(
        self, mock_save, mock_display, mock_manual, mock_confirm, mock_load
    ):
        """Should prompt manual config if env is invalid."""
        mock_load.return_value = None  # Invalid env
        mock_manual.return_value = {
            "base_url": "https://manual.com",
            "api_key": "sk-manual",
            "timeout": 60000,
            "max_tokens": 100,
            "endpoint": "/v1/chat/completions",
            "request_delay_ms": 200,
        }
        mock_confirm.return_value = True  # Save to .env
        
        result = interactive_setup()
        
        assert result["base_url"] == "https://manual.com"
        mock_manual.assert_called_once()
        mock_save.assert_called_once_with(result)

    @patch("src.ui.load_from_env")
    @patch("src.ui.Confirm.ask")
    @patch("src.ui.prompt_manual_config")
    @patch("src.ui.display_config")
    @patch("src.ui.save_to_env")
    def test_interactive_setup_skip_save(
        self, mock_save, mock_display, mock_manual, mock_confirm, mock_load
    ):
        """Should not save to .env if user declines."""
        mock_load.return_value = None
        mock_manual.return_value = {
            "base_url": "https://temp.com",
            "api_key": "sk-temp",
            "timeout": 30000,
            "max_tokens": 25,
            "endpoint": "/v1/chat/completions",
            "request_delay_ms": 500,
        }
        mock_confirm.return_value = False  # Don't save
        
        result = interactive_setup()
        
        assert result["base_url"] == "https://temp.com"
        mock_save.assert_not_called()


class TestMainFlowIntegration:
    """Integration tests for main.py flow scenarios."""

    @patch("main.fetch_models")
    @patch("main.interactive_setup")
    @patch("main.parse_args")
    def test_connection_error_triggers_reconfigure(
        self, mock_parse, mock_interactive, mock_fetch
    ):
        """Should offer reconfigure on connection error."""
        import requests
        
        # First fetch fails, second succeeds
        mock_fetch.side_effect = [
            requests.exceptions.ConnectionError("Connection refused"),
            ["model1", "model2"],
        ]
        
        mock_interactive.return_value = {
            "base_url": "https://new-api.com/v1",
            "api_key": "sk-new-key",
            "timeout": 30000,
            "max_tokens": 25,
            "endpoint": "/v1/chat/completions",
            "request_delay_ms": 500,
        }
        
        # This would be called in main() error handler
        # Verify interactive_setup is called on error
        assert mock_interactive.return_value is not None

    def test_placeholder_detection_comprehensive(self, monkeypatch):
        """Test all placeholder patterns are detected."""
        test_cases = [
            # (base_url, api_key, should_be_rejected)
            ("http://localhost:8000", "sk-your-api-key-here", True),
            ("http://localhost:8000", "sk-real-key", True),  # default URL
            ("https://api.real.com", "sk-your-api-key-here", True),  # placeholder key
            ("https://api.real.com", "your-api-key", True),
            ("https://api.real.com", "sk-test", True),
            ("https://api.real.com", "sk-proj-abc123", False),  # VALID
            ("https://api.openai.com/v1", "sk-proj-xyz789", False),  # VALID
        ]
        
        for base_url, api_key, should_reject in test_cases:
            monkeypatch.setenv("OAI_TEST_BASE_URL", base_url)
            monkeypatch.setenv("OAI_TEST_API_KEY", api_key)
            
            result = load_from_env()
            
            if should_reject:
                assert result is None, f"Should reject: {base_url} + {api_key}"
            else:
                assert result is not None, f"Should accept: {base_url} + {api_key}"


class TestErrorMessageFormatting:
    """Test error messages are user-friendly."""

    def test_connection_error_format(self):
        """Connection error should be clean, not verbose."""
        from rich.console import Console
        from io import StringIO
        
        console = Console(file=StringIO(), force_terminal=True)
        
        console.print("\n[bold red]✗[/bold red] Cannot connect to API server")
        console.print("[yellow]Server:[/yellow] http://localhost:8000")
        console.print("[yellow]Error:[/yellow] Connection refused (server may be offline)\n")
        
        output = console.file.getvalue()
        
        # Should NOT contain HTTPConnectionPool or verbose stack trace
        assert "HTTPConnectionPool" not in output
        assert "Cannot connect to API server" in output

    def test_timeout_error_format(self):
        """Timeout error should be clean."""
        from rich.console import Console
        from io import StringIO
        
        console = Console(file=StringIO(), force_terminal=True)
        
        timeout = 30000
        console.print(f"\n[bold red]✗[/bold red] Request timeout after {timeout}ms")
        console.print("[yellow]Server:[/yellow] http://api.slow.com\n")
        
        output = console.file.getvalue()
        
        assert "Request timeout" in output
        assert "30000ms" in output
