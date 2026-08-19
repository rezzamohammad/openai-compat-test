#!/usr/bin/env python3
"""
OpenAI-compatible API tester with retry and exponential backoff.
"""
import sys
import time
import requests
from src.config import load_env_file, parse_args, normalize_base_url, build_completions_url
from src.client import fetch_models
from src.runner import run_tests
from src.retry import RetryConfig
from src.output import (
    print_models_header, print_summary, render_results, output_results, OutputConfig
)
from src.ui import interactive_setup, display_config, prompt_model_selection, confirm_ready, print_header
from rich.console import Console
from rich.prompt import Confirm

console = Console()


def main() -> int:
    load_env_file(".env")
    args = parse_args()

    # Set output config
    OutputConfig.no_json = args.no_json
    OutputConfig.output_file = args.output_file

    # Check if we have actual CLI arguments (not just from env)
    has_explicit_cli_args = any(
        arg.startswith(('--api-key', '--base-url', '--models'))
        for arg in sys.argv[1:]
    )

    # If no CLI args provided, run interactive setup
    # interactive_setup() will handle placeholder detection internally
    if not has_explicit_cli_args and not args.api_key and not args.base_url:
        # Run interactive setup - will detect placeholders and prompt user
        config = interactive_setup()

        base_url = config.get("base_url", "")
        api_key = config.get("api_key", "")
        max_tokens = config.get("max_tokens", 25)
        endpoint = config.get("endpoint", "/v1/chat/completions")
        timeout = config.get("timeout", 30000)
        request_delay_ms = config.get("request_delay_ms", 500)
        use_interactive_model_selection = True
    else:
        # Use CLI args/env
        base_url = args.base_url
        api_key = args.api_key
        max_tokens = args.max_tokens
        endpoint = args.endpoint
        timeout = args.timeout
        request_delay_ms = args.request_delay_ms
        use_interactive_model_selection = False

    if not api_key:
        print("Missing API key. Set --api-key or OAI_TEST_API_KEY.", file=sys.stderr)
        return 2

    if not base_url:
        print("Missing base URL. Set --base-url or OAI_TEST_BASE_URL.", file=sys.stderr)
        return 2

    base_url = normalize_base_url(base_url)
    completions_url = build_completions_url(base_url, endpoint)
    session = requests.Session()

    try:
        models = args.models or fetch_models(base_url, api_key, session, timeout)
    except requests.exceptions.ConnectionError:
        console.print("\n[bold red]✗ Cannot connect to API server[/bold red]")
        console.print(f"[yellow]Server:[/yellow] {base_url}")
        console.print("[yellow]Error:[/yellow] Connection refused (server may be offline)\n")
        
        # Offer to reconfigure
        if Confirm.ask("[bold]Configure a different API?[/bold]", default=True):
            config = interactive_setup()
            base_url = config.get("base_url", "")
            api_key = config.get("api_key", "")
            max_tokens = config.get("max_tokens", 25)
            endpoint = config.get("endpoint", "/v1/chat/completions")
            timeout = config.get("timeout", 30000)
            request_delay_ms = config.get("request_delay_ms", 500)
            
            # Retry with new config - don't use old args.models
            try:
                models = fetch_models(base_url, api_key, session, timeout)
            except Exception as retry_exc:
                console.print(f"\n[bold red]✗[/bold red] Failed to fetch models: {retry_exc}")
                return 1
        else:
            return 1
    except requests.exceptions.Timeout:
        console.print(f"\n[bold red]✗[/bold red] Request timeout after {timeout}ms")
        console.print(f"[yellow]Server:[/yellow] {base_url}\n")
        return 1
    except Exception as exc:
        console.print(f"\n[bold red]✗[/bold red] Failed to fetch models")
        console.print(f"[yellow]Error:[/yellow] {exc}\n")
        return 1

    if not models:
        print("No models found.", file=sys.stderr)
        return 1

    # If using interactive mode and no explicit model selection, let user select models
    if use_interactive_model_selection and not args.models:
        models = prompt_model_selection(models)

        if not confirm_ready(models, {
            "base_url": base_url,
            "api_key": api_key,
            "timeout": timeout,
            "max_tokens": max_tokens,
            "endpoint": endpoint,
            "request_delay_ms": request_delay_ms,
        }):
            return 1
    else:
        print_models_header(models)

    delay = max(request_delay_ms, 0) / 1000.0

    # Configure retry with more conservative settings for mass testing
    retry_config = RetryConfig(
        max_attempts=2,  # Reduce to 2 attempts for faster feedback
        initial_delay=0.5,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True,
        retryable_status_codes=[429, 502, 503, 504]  # Only retry server errors
    )

    total_start = time.time()
    results = run_tests(
        models, completions_url, api_key, max_tokens,
        session, timeout, args.verbose, delay,
        enable_retry=True,
        retry_config=retry_config
    )
    total_ms = int((time.time() - total_start) * 1000)

    if args.verbose:
        print_summary(results, total_ms)

    json_results = render_results(results)
    output_results(json_results)

    failed = [r for r in results if not r.ok]

    # Print failure summary
    if failed:
        print(f"\n{len(failed)}/{len(results)} models failed", file=sys.stderr)

        # Group failures by error type
        error_groups = {}
        for r in failed:
            error_type = r.error.split(':')[0] if r.error else 'unknown'
            if error_type not in error_groups:
                error_groups[error_type] = []
            error_groups[error_type].append(r.model)

        print("\nFailure breakdown:", file=sys.stderr)
        for error_type, model_list in sorted(error_groups.items(), key=lambda x: -len(x[1])):
            print(f"  {error_type}: {len(model_list)} models", file=sys.stderr)
    else:
        print(f"\n✓ All {len(results)} models passed!", file=sys.stderr)

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
