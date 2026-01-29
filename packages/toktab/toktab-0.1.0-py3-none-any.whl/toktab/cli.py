"""TokTab CLI - LLM pricing data at your fingertips."""

import click

from toktab import __version__
from toktab.api import (
    get_model,
    search as api_search,
    ModelNotFoundError,
    APIError,
)
from toktab.display import (
    display_model,
    display_search_results,
    display_error,
)


class TokTabGroup(click.Group):
    """Custom group that allows both subcommands and direct model lookup."""

    def get_command(self, ctx, cmd_name):
        """Override get_command to handle model lookups."""
        # First try to get a real subcommand
        rv = super().get_command(ctx, cmd_name)
        if rv is not None:
            return rv

        # If no subcommand found, create a dynamic command for model lookup
        @click.pass_context
        def model_lookup_command(ctx_inner):
            json_output = ctx.params.get('json_output', False)
            try:
                data = get_model(cmd_name)
                display_model(data, json_output=json_output)
            except ModelNotFoundError as e:
                display_error(str(e))
                ctx_inner.exit(1)
            except APIError as e:
                display_error(str(e))
                ctx_inner.exit(1)

        return click.Command(cmd_name, callback=model_lookup_command)


@click.command(cls=TokTabGroup, invoke_without_command=True)
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON")
@click.option("--version", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx: click.Context, json_output: bool, version: bool) -> None:
    """TokTab - LLM pricing data at your fingertips.

    Get pricing info for a model:

        toktab gpt-4o

    Search for models:

        toktab search claude
    """
    if version:
        click.echo(f"toktab {__version__}")
        ctx.exit(0)

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", default=20, help="Number of results (max 50)")
@click.option("--json", "json_output", is_flag=True, help="Output raw JSON")
def search(query: str, limit: int, json_output: bool) -> None:
    """Search for models by name or provider.

    Examples:

        toktab search claude

        toktab search "gemini 3"

        toktab search provider:anthropic

        toktab search "provider:openai gpt-4"
    """
    try:
        data = api_search(query, limit=limit)
        display_search_results(data, json_output=json_output)
    except APIError as e:
        display_error(str(e))
        raise SystemExit(1)


if __name__ == "__main__":
    cli()
