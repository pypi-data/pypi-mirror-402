"""CLI interface for AM4 Prices."""

from datetime import datetime, timezone
from typing import Optional

import typer
from rich.console import Console

from . import __version__
from .api import AM4APIClient
from .ui import PriceUI

app = typer.Typer(
    name="am4-prices",
    help="A sleek CLI client for Airline Manager 4 Fuel/CO2 prices",
    add_completion=False,
)

console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"am4-prices version: [cyan]{__version__}[/cyan]")
        raise typer.Exit()


@app.command()
def show(
    day: int = typer.Option(
        1,
        "--day",
        "-d",
        min=1,
        max=30,
        help="Day number to display prices for (1-30)",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help="Custom API URL to fetch prices from",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Display current and upcoming fuel/CO2 prices for Airline Manager 4.

    The prices are fetched from the AM4 Helper database and displayed
    in a beautiful terminal interface.

    Examples:

        # Show prices for day 1 (default)
        $ am4-prices show

        # Show prices for day 15
        $ am4-prices show --day 15

        # Use custom API URL
        $ am4-prices show --url https://example.com/prices.json
    """
    ui = PriceUI(console=console)

    try:
        # Show loading message
        ui.show_loading()

        # Fetch prices
        with AM4APIClient(base_url=url) as client:
            prices_data = client.fetch_prices()

        # Get prices for specified day
        day_prices = prices_data.get_day(day)

        # Display prices (use UTC to match price timestamps)
        current_time = datetime.now(timezone.utc)
        ui.display_prices(day_prices, current_time)

        # Show success message
        console.print(
            f"\n[dim]Showing prices for Day {day}. "
            "Press Ctrl+C to exit or run again to refresh.[/dim]\n"
        )

    except Exception as e:
        ui.show_error(str(e))
        console.print(
            "[yellow]Tip:[/yellow] Make sure you have an internet connection "
            "and the API is accessible.\n"
        )
        raise typer.Exit(code=1)


@app.command()
def watch(
    day: int = typer.Option(
        1,
        "--day",
        "-d",
        min=1,
        max=30,
        help="Day number to watch prices for (1-30)",
    ),
    interval: int = typer.Option(
        60,
        "--interval",
        "-i",
        min=10,
        max=3600,
        help="Refresh interval in seconds (10-3600)",
    ),
    url: Optional[str] = typer.Option(
        None,
        "--url",
        "-u",
        help="Custom API URL to fetch prices from",
    ),
) -> None:
    """Watch prices in real-time with auto-refresh.

    This command will continuously display the current prices
    and refresh them at the specified interval.

    Examples:

        # Watch prices with default 60s interval
        $ am4-prices watch

        # Watch prices with 30s interval
        $ am4-prices watch --interval 30

        # Watch day 10 prices
        $ am4-prices watch --day 10
    """
    import time

    ui = PriceUI(console=console)

    try:
        console.print(
            f"\n[cyan]Watching AM4 prices (Day {day}) - Refreshing every {interval}s[/cyan]"
        )
        console.print("[dim]Press Ctrl+C to exit[/dim]\n")

        while True:
            try:
                # Fetch prices
                with AM4APIClient(base_url=url) as client:
                    prices_data = client.fetch_prices()

                # Get prices for specified day
                day_prices = prices_data.get_day(day)

                # Display prices
                current_time = datetime.now()
                ui.display_prices(day_prices, current_time)

                # Wait for next refresh
                time.sleep(interval)

            except KeyboardInterrupt:
                console.print("\n[yellow]Watch mode stopped.[/yellow]\n")
                raise typer.Exit()

            except Exception as e:
                ui.show_error(str(e))
                console.print(f"[yellow]Retrying in {interval} seconds...[/yellow]\n")
                time.sleep(interval)

    except typer.Exit:
        raise
    except Exception as e:
        ui.show_error(str(e))
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """AM4 Prices - A sleek CLI client for Airline Manager 4 Fuel/CO2 prices.

    Run 'am4-prices show' to display current prices or 'am4-prices watch'
    for real-time monitoring.
    """
    if ctx.invoked_subcommand is None:
        # Default to show command if no subcommand provided
        ctx.invoke(show)


if __name__ == "__main__":
    app()
