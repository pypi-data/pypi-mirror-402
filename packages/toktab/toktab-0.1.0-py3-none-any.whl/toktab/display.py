"""Display formatting for TokTab CLI using Rich."""

import json
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()


def format_cost(cost_per_token: float | None) -> str:
    """Format cost per token as cost per million tokens.

    Args:
        cost_per_token: Cost in dollars per token, or None.

    Returns:
        Formatted string like '$0.50' or 'Free' or '-'.
    """
    if cost_per_token is None:
        return "-"
    if cost_per_token == 0:
        return "Free"
    cost_per_million = cost_per_token * 1_000_000
    if cost_per_million < 0.01:
        return f"${cost_per_million:.4f}"
    elif cost_per_million < 1:
        # Format and strip trailing zeros
        formatted = f"{cost_per_million:.2f}"
        return f"${formatted.rstrip('0').rstrip('.')}"
    else:
        return f"${cost_per_million:.2f}"


def format_tokens(tokens: int | None) -> str:
    """Format token count in a human-readable way.

    Args:
        tokens: Number of tokens, or None.

    Returns:
        Formatted string like '128K' or '1M' or '-'.
    """
    if tokens is None:
        return "-"
    if tokens >= 1_000_000:
        value = tokens / 1_000_000
        if value == int(value):
            return f"{int(value)}M"
        return f"{value:.1f}M".rstrip("0").rstrip(".")
    elif tokens >= 1_000:
        value = tokens / 1_000
        if value == int(value):
            return f"{int(value)}K"
        return f"{value:.1f}K".rstrip("0").rstrip(".")
    return str(tokens)


def get_cost_style(cost_per_token: float | None) -> str:
    """Get Rich style based on cost tier.

    Args:
        cost_per_token: Cost in dollars per token.

    Returns:
        Rich style string.
    """
    if cost_per_token is None or cost_per_token == 0:
        return "green"
    cost_per_million = cost_per_token * 1_000_000
    if cost_per_million < 1:
        return "green"
    elif cost_per_million < 10:
        return "yellow"
    else:
        return "red"


def display_model(data: dict[str, Any], json_output: bool = False) -> None:
    """Display detailed model information.

    Args:
        data: Model data from the API.
        json_output: If True, output raw JSON instead of formatted table.
    """
    if json_output:
        console.print(json.dumps(data, indent=2))
        return

    # Model header
    name = data.get("litellm_model_name", data.get("slug", "Unknown"))
    provider = data.get("litellm_provider", "Unknown")

    title = Text()
    title.append(name, style="bold cyan")
    title.append(f" ({provider})", style="dim")

    # Pricing table
    pricing_table = Table(show_header=True, header_style="bold", box=None)
    pricing_table.add_column("Type", style="dim")
    pricing_table.add_column("Cost / 1M tokens", justify="right")

    input_cost = data.get("input_cost_per_token")
    output_cost = data.get("output_cost_per_token")

    pricing_table.add_row(
        "Input", Text(format_cost(input_cost), style=get_cost_style(input_cost))
    )
    pricing_table.add_row(
        "Output", Text(format_cost(output_cost), style=get_cost_style(output_cost))
    )

    # Add cache costs if present
    if cache_read := data.get("cache_read_input_token_cost"):
        pricing_table.add_row(
            "Cache read", Text(format_cost(cache_read), style=get_cost_style(cache_read))
        )
    if cache_write := data.get("cache_creation_input_token_cost"):
        pricing_table.add_row(
            "Cache write",
            Text(format_cost(cache_write), style=get_cost_style(cache_write)),
        )

    # Context window
    context_table = Table(show_header=True, header_style="bold", box=None)
    context_table.add_column("Limit", style="dim")
    context_table.add_column("Tokens", justify="right")

    if max_input := data.get("max_input_tokens"):
        context_table.add_row("Max input", format_tokens(max_input))
    if max_output := data.get("max_output_tokens"):
        context_table.add_row("Max output", format_tokens(max_output))
    if max_tokens := data.get("max_tokens"):
        context_table.add_row("Max total", format_tokens(max_tokens))

    # Capabilities
    capabilities = []
    capability_fields = [
        ("supports_vision", "Vision"),
        ("supports_function_calling", "Functions"),
        ("supports_tool_choice", "Tool choice"),
        ("supports_prompt_caching", "Caching"),
        ("supports_response_schema", "Schema"),
        ("supports_system_messages", "System msgs"),
        ("supports_audio_input", "Audio in"),
        ("supports_audio_output", "Audio out"),
        ("supports_pdf_input", "PDF"),
    ]

    for field, label in capability_fields:
        if data.get(field):
            capabilities.append(label)

    # Build output
    console.print()
    console.print(Panel(title, border_style="cyan"))
    console.print()

    console.print("[bold]Pricing[/bold]")
    console.print(pricing_table)
    console.print()

    if context_table.row_count > 0:
        console.print("[bold]Context Window[/bold]")
        console.print(context_table)
        console.print()

    if capabilities:
        console.print("[bold]Capabilities[/bold]")
        cap_text = " · ".join(f"[green]✓[/green] {c}" for c in capabilities)
        console.print(cap_text)
        console.print()


def display_search_results(data: dict[str, Any], json_output: bool = False) -> None:
    """Display search results.

    Args:
        data: Search response from the API.
        json_output: If True, output raw JSON instead of formatted table.
    """
    if json_output:
        console.print(json.dumps(data, indent=2))
        return

    results = data.get("results", [])
    count = data.get("count", len(results))
    query = data.get("query", "")

    if not results:
        console.print(f"[yellow]No models found for '{query}'[/yellow]")
        return

    console.print()
    console.print(f"[dim]Found {count} model(s) for '{query}'[/dim]")
    console.print()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Model", style="cyan")
    table.add_column("Provider", style="dim")
    table.add_column("Input / 1M", justify="right")
    table.add_column("Output / 1M", justify="right")

    for model in results:
        input_cost = model.get("input_cost_per_token")
        output_cost = model.get("output_cost_per_token")

        table.add_row(
            model.get("slug", model.get("name", "?")),
            model.get("provider", "-"),
            Text(format_cost(input_cost), style=get_cost_style(input_cost)),
            Text(format_cost(output_cost), style=get_cost_style(output_cost)),
        )

    console.print(table)
    console.print()


def display_providers(providers: list[str], json_output: bool = False) -> None:
    """Display list of providers.

    Args:
        providers: List of provider names.
        json_output: If True, output raw JSON instead of formatted list.
    """
    if json_output:
        console.print(json.dumps(providers, indent=2))
        return

    console.print()
    console.print(f"[bold]Providers[/bold] ({len(providers)})")
    console.print()

    for provider in providers:
        console.print(f"  • {provider}")

    console.print()
    console.print("[dim]Tip: Search by provider with 'toktab search provider:NAME'[/dim]")
    console.print()


def display_error(message: str) -> None:
    """Display an error message.

    Args:
        message: The error message to display.
    """
    console.print(f"[red]Error:[/red] {message}")
