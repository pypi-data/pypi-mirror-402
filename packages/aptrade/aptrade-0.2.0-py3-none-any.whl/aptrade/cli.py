from pathlib import Path
from typing import Any, Dict

import typer
import uvicorn

from aptrade.backtest import run_backtest
from aptrade.version import VERSION as APP_VERSION

APP_AUTHOR = "Victor Caldas"
APP_COPYRIGHT = "2025-2025"

CLI_HELP_TEXT = (
    "APTrade Command Line Interface\n\n"
    f"Author: {APP_AUTHOR}\n"
    f"Years: {APP_COPYRIGHT}\n"
    f"Version: {APP_VERSION}"
)

cli = typer.Typer(help=CLI_HELP_TEXT, no_args_is_help=True)


@cli.command()
def server(
    dev: bool = typer.Option(
        False, "--dev", "-d", help="Run server in development mode (with reload)"
    ),
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
):
    """Start the APTrade Server."""
    module = "aptrade.main:app"
    if dev:
        uvicorn.run(module, host=host, port=port, reload=True, reload_dirs=["aptrade"])
    else:
        uvicorn.run(module, host=host, port=port)


@cli.command()
def backtest(
    yaml_file: Path = typer.Argument(
        ...,
        exists=True,
        dir_okay=False,
        readable=True,
        help="Path to backtest YAML configuration",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Enable verbose output and keep running after individual ticker failures",
    ),
):
    """Run backtests described in the given YAML configuration."""

    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - CLI safety net
        typer.secho(
            "PyYAML is required to load the configuration. Install it with 'pip install PyYAML'.",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1) from exc

    try:
        config_data: Dict[str, Any] = yaml.safe_load(yaml_file.read_text()) or {}
    except Exception as exc:  # pragma: no cover - defensive parsing
        raise typer.BadParameter(
            f"Failed to parse '{yaml_file}': {exc}",
            param_hint="yaml_file",
        ) from exc

    if not isinstance(config_data, dict):
        raise typer.BadParameter(
            "Backtest configuration must be a mapping.", param_hint="yaml_file"
        )

    results = run_backtest(config=config_data, debug=debug)

    if not results:
        typer.echo("No backtest results generated.")
        raise typer.Exit(code=0)

    typer.echo("Ticker\tReturn (%)")
    for ticker, ret in sorted(results.items()):
        typer.echo(f"{ticker}\t{ret * 100:.2f}")


if __name__ == "__main__":
    cli()
