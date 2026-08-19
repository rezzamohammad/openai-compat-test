import argparse
import os
import pathlib
from typing import Optional


def load_env_file(path: Optional[str] = None) -> None:
    p = path or ".env"
    file = pathlib.Path(p)

    if not file.exists():
        return

    for line in file.read_text(encoding="utf-8").splitlines():
        s = line.strip()

        if not s or s.startswith("#"):
            continue

        if "=" not in s:
            continue

        k, v = s.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")

        if k and k not in os.environ:
            os.environ[k] = v


def normalize_base_url(base_url: str) -> str:
    """Normalize base URL by stripping trailing slashes."""
    return base_url.rstrip("/")


def build_completions_url(base_url: str, endpoint: str) -> str:
    """Build full URL, avoiding double /v1/v1/ paths"""
    # Normalize endpoint to start with /
    path = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    
    # If base_url ends with /v1 and endpoint starts with /v1, remove one /v1
    if base_url.endswith("/v1") and path.startswith("/v1"):
        base_url = base_url[:-3]  # Remove /v1 from base_url
    
    return f"{base_url}{path}"


def get_env_var(key: str, default: str = "") -> str:
    """Get environment variable with default value."""
    return os.environ.get(key) or default


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test OpenAI-compatible API models with comprehensive validation.",
        prog="OpenAI Compatible API Tester"
    )
    
    # Environment variable names: OAI_TEST_*
    parser.add_argument(
        "--base-url",
        default=get_env_var("OAI_TEST_BASE_URL")
    )
    parser.add_argument(
        "--api-key",
        default=get_env_var("OAI_TEST_API_KEY")
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=int(get_env_var("OAI_TEST_MAX_TOKENS", "25"))
    )
    parser.add_argument(
        "--endpoint",
        default=get_env_var("OAI_TEST_COMPLETIONS_PATH", "/chat/completions")
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(get_env_var("OAI_TEST_TIMEOUT", "30000"))
    )
    parser.add_argument(
        "--request-delay-ms",
        type=int,
        default=int(get_env_var("OAI_TEST_REQUEST_DELAY_MS", "500"))
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=get_env_var("OAI_TEST_VERBOSE") in ("1", "true", "True"),
        help="Show detailed logs for each model test"
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        default=False,
        help="Don't print JSON output (shows colored report only)"
    )
    parser.add_argument(
        "--output-file",
        default=None,
        help="Save JSON results to file instead of stdout"
    )
    parser.add_argument(
        "--models",
        nargs="*",
        default=None
    )

    return parser.parse_args()
