"""Interactive TUI for API configuration setup."""
import os
from typing import List, Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.text import Text


console = Console()


def mask_api_key(api_key: str) -> str:
    """Mask API key for display."""
    if len(api_key) <= 8:
        return "***"
    return api_key[:6] + "..." + api_key[-2:]


def print_header() -> None:
    """Print beautiful header."""
    title = "OpenAI Compatible API Tester - Setup"
    console.print(Panel.fit(
        f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2)
    ))


def prompt_use_env() -> bool:
    """Ask if user wants to use environment variables."""
    console.print("\n[bold]Configuration Mode[/bold]")
    return Confirm.ask(
        "Use environment variables / .env file?",
        default=True
    )


def save_to_env(config: Dict[str, Any], env_path: str = ".env") -> None:
    """Save configuration to .env file.
    
    Args:
        config: Configuration dictionary
        env_path: Path to .env file (default: .env)
    """
    import pathlib
    
    env_file = pathlib.Path(env_path)
    
    # Create .env content
    content = f"""# OpenAI Compatible API Tester Configuration

# API Settings (required)
OAI_TEST_BASE_URL={config['base_url']}
OAI_TEST_API_KEY={config['api_key']}

# Request Settings (optional)
OAI_TEST_MAX_TOKENS={config['max_tokens']}
OAI_TEST_COMPLETIONS_PATH={config['endpoint']}
OAI_TEST_TIMEOUT={config['timeout']}
OAI_TEST_REQUEST_DELAY_MS={config['request_delay_ms']}
"""
    
    # Write to file
    with open(env_file, 'w') as f:
        f.write(content)
    
    console.print(f"[bold green]✓[/bold green] Configuration saved to [cyan]{env_path}[/cyan]")


def load_from_env() -> Optional[Dict[str, Any]]:
    """Load configuration from environment variables."""
    base_url = os.environ.get("OAI_TEST_BASE_URL")
    api_key = os.environ.get("OAI_TEST_API_KEY")

    # Don't load if values are missing or placeholders
    if not base_url or not api_key:
        return None
    
    # Detect placeholder/default values
    placeholder_keys = ["sk-your-api-key-here", "your-api-key", "sk-test", "sk-your-key-here"]
    default_urls = ["http://localhost:8000"]
    
    if api_key in placeholder_keys or base_url in default_urls:
        return None

    return {
        "base_url": base_url,
        "api_key": api_key,
        "timeout": int(os.environ.get("OAI_TEST_TIMEOUT", 30000)),
        "max_tokens": int(os.environ.get("OAI_TEST_MAX_TOKENS", 25)),
        "endpoint": os.environ.get("OAI_TEST_COMPLETIONS_PATH", "/v1/chat/completions"),
        "request_delay_ms": int(os.environ.get("OAI_TEST_REQUEST_DELAY_MS", 500)),
    }


def prompt_manual_config() -> Dict[str, Any]:
    """Prompt user for manual API configuration."""
    console.print("\n[bold]API Configuration[/bold]")

    base_url = Prompt.ask(
        "Base URL",
        default=os.environ.get("OAI_TEST_BASE_URL", "http://localhost:8000")
    )

    # API Key is REQUIRED - loop until user provides one
    api_key = ""
    while not api_key or api_key.strip() == "":
        api_key = Prompt.ask(
            "API Key [red](required)[/red]",
            password=False
        )
        if not api_key or api_key.strip() == "":
            console.print("[red]✗ API Key is required. Please enter a valid key.[/red]")

    timeout = Prompt.ask(
        "Timeout (ms)",
        default=os.environ.get("OAI_TEST_TIMEOUT", "30000"),
        console=console
    )

    max_tokens = Prompt.ask(
        "Max Tokens",
        default=os.environ.get("OAI_TEST_MAX_TOKENS", "25"),
        console=console
    )

    endpoint = Prompt.ask(
        "Completions Endpoint",
        default=os.environ.get("OAI_TEST_COMPLETIONS_PATH", "/v1/chat/completions")
    )

    request_delay_ms = Prompt.ask(
        "Request Delay (ms)",
        default=os.environ.get("OAI_TEST_REQUEST_DELAY_MS", "500"),
        console=console
    )

    return {
        "base_url": base_url,
        "api_key": api_key.strip(),
        "timeout": int(timeout),
        "max_tokens": int(max_tokens),
        "endpoint": endpoint,
        "request_delay_ms": int(request_delay_ms),
    }


def display_config(config: Dict[str, Any]) -> None:
    """Display current configuration in a nice table."""
    table = Table(title="[bold cyan]API Settings[/bold cyan]", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Base URL", config.get("base_url", "N/A"))
    table.add_row("API Key", mask_api_key(config.get("api_key", "")))
    table.add_row("Timeout", f"{config.get('timeout', 30000)}ms")
    table.add_row("Max Tokens", str(config.get("max_tokens", 25)))
    table.add_row("Endpoint", config.get("endpoint", "/v1/chat/completions"))
    table.add_row("Request Delay", f"{config.get('request_delay_ms', 500)}ms")

    console.print(table)


def prompt_model_selection(available_models: List[str]) -> List[str]:
    """Prompt user to select which models to test."""
    if not available_models:
        console.print("[yellow]No models available[/yellow]")
        return []

    console.print("\n[bold]Model Selection[/bold]")
    console.print(f"[dim]Found {len(available_models)} model(s)[/dim]\n")

    # Simple prompt-based selection for compatibility
    use_all = Confirm.ask(
        "Test all available models?",
        default=True
    )

    if use_all:
        return available_models

    # Show models and let user select
    selected = []
    for i, model in enumerate(available_models, 1):
        if Confirm.ask(f"Test {model}?", default=False):
            selected.append(model)

    return selected if selected else available_models


def confirm_ready(selected_models: List[str], config: Dict[str, Any]) -> bool:
    """Show final confirmation before starting tests."""
    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]")
    console.print(f"[bold]Ready to test {len(selected_models)} model(s)[/bold]\n")

    display_config(config)

    console.print("\n[bold cyan]Models to Test:[/bold cyan]")
    for i, model in enumerate(selected_models, 1):
        console.print(f"  {i}. [cyan]{model}[/cyan]")

    console.print("\n[bold cyan]═══════════════════════════════════════[/bold cyan]\n")

    return Confirm.ask("Proceed with testing?", default=True)


def interactive_setup() -> Dict[str, Any]:
    """Run complete interactive setup flow.

    Returns:
        Dictionary with keys: base_url, api_key, timeout, max_tokens, endpoint, request_delay_ms
    """
    print_header()

    # Try to load from env first
    env_config = load_from_env()

    if env_config:
        console.print("\n[bold green]✓[/bold green] Loaded configuration from environment")
        display_config(env_config)

        use_env = Confirm.ask(
            "\n[bold]Use these settings?[/bold]",
            default=True
        )

        if use_env:
            return env_config

    # Otherwise prompt for manual entry
    console.print("\n[bold yellow]Manual Configuration Required[/bold yellow]")
    config = prompt_manual_config()

    display_config(config)

    # Ask if user wants to save to .env
    if Confirm.ask("\n[bold]Save this configuration to .env file?[/bold]", default=True):
        save_to_env(config)

    return config

