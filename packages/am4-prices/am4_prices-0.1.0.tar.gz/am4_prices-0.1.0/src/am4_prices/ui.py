"""Terminal UI components for displaying AM4 prices."""

from datetime import datetime, timezone
from typing import Optional

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import DayPrices, PricePoint


class PriceUI:
    """UI handler for displaying price information."""

    def __init__(self, console: Optional[Console] = None):
        """Initialize the UI.

        Args:
            console: Rich console instance (creates new one if not provided)
        """
        self.console = console or Console()

    def create_header(self) -> Panel:
        """Create the header panel."""
        header_text = Text()
        header_text.append("✈️  ", style="bold cyan")
        header_text.append("AM4 Fuel & CO2 Prices", style="bold white")
        header_text.append("  ✈️", style="bold cyan")

        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        subtitle = Text(f"Updated: {current_time}", style="dim")

        return Panel(
            Text.assemble(header_text, "\n", subtitle, justify="center"),
            box=box.DOUBLE,
            style="cyan",
        )

    def create_current_price_panel(self, price: PricePoint) -> Panel:
        """Create panel for current price.

        Args:
            price: Current price point

        Returns:
            Rich Panel with current price information
        """
        fuel_color = self._get_fuel_color(price.fuel)
        co2_color = self._get_co2_color(price.co2)

        content = Text()
        content.append("⏰ Time: ", style="bold white")
        content.append(f"{price.time[:5]}\n\n", style="yellow")

        content.append("⛽ Fuel:  ", style="bold white")
        content.append(f"${price.fuel:,}\n", style=f"bold {fuel_color}")

        content.append("🌍 CO2:   ", style="bold white")
        content.append(f"${price.co2:,}", style=f"bold {co2_color}")

        return Panel(
            content,
            title="[bold]Current Prices[/bold]",
            border_style="green",
            box=box.ROUNDED,
        )

    def create_upcoming_table(self, prices: list[PricePoint]) -> Table:
        """Create table for upcoming prices.

        Args:
            prices: List of upcoming price points

        Returns:
            Rich Table with upcoming prices
        """
        table = Table(
            title="📈 Upcoming Prices",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold cyan",
            border_style="blue",
        )

        table.add_column("Time", style="yellow", justify="center", width=10)
        table.add_column("Fuel", justify="right", width=12)
        table.add_column("CO2", justify="right", width=12)
        table.add_column("Status", justify="center", width=10)

        for price in prices:
            fuel_color = self._get_fuel_color(price.fuel)
            co2_color = self._get_co2_color(price.co2)

            # Determine if prices are good
            fuel_status = "✓" if price.fuel < 550 else "→" if price.fuel < 800 else "✗"
            co2_status = "✓" if price.co2 < 130 else "→" if price.co2 < 150 else "✗"

            status_color = (
                "green"
                if fuel_status == "✓" and co2_status == "✓"
                else "yellow"
                if fuel_status != "✗" and co2_status != "✗"
                else "red"
            )

            table.add_row(
                price.time[:5],
                f"[{fuel_color}]${price.fuel:,}[/{fuel_color}]",
                f"[{co2_color}]${price.co2:,}[/{co2_color}]",
                f"[{status_color}]{fuel_status}{co2_status}[/{status_color}]",
            )

        return table

    def create_price_legend(self) -> Panel:
        """Create legend explaining price colors.

        Returns:
            Rich Panel with legend information
        """
        legend = Text()
        legend.append("Price Guide:\n\n", style="bold white")

        legend.append("⛽ Fuel:  ", style="bold white")
        legend.append("<$550 ", style="bold green")
        legend.append("Good  ", style="dim")
        legend.append("$550-800 ", style="bold yellow")
        legend.append("OK  ", style="dim")
        legend.append(">$800 ", style="bold red")
        legend.append("High\n", style="dim")

        legend.append("🌍 CO2:   ", style="bold white")
        legend.append("<$130 ", style="bold green")
        legend.append("Good  ", style="dim")
        legend.append("$130-150 ", style="bold yellow")
        legend.append("OK  ", style="dim")
        legend.append(">$150 ", style="bold red")
        legend.append("High\n\n", style="dim")

        legend.append("Status: ", style="bold white")
        legend.append("✓ Good  ", style="green")
        legend.append("→ OK  ", style="yellow")
        legend.append("✗ High", style="red")

        return Panel(legend, title="[bold]Legend[/bold]", border_style="magenta")

    def display_prices(self, day_prices: DayPrices, current_time: datetime) -> None:
        """Display current and upcoming prices.

        Args:
            day_prices: Prices for the current day
            current_time: Current datetime
        """
        self.console.clear()

        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="main"),
            Layout(name="legend", size=12),
        )

        layout["main"].split_row(
            Layout(name="current", ratio=1),
            Layout(name="upcoming", ratio=2),
        )

        # Get data
        current_price = day_prices.get_current_price(current_time)
        upcoming_prices = day_prices.get_upcoming_prices(current_time, count=10)

        # Populate layout
        layout["header"].update(self.create_header())
        layout["current"].update(self.create_current_price_panel(current_price))
        layout["upcoming"].update(self.create_upcoming_table(upcoming_prices))
        layout["legend"].update(self.create_price_legend())

        # Print layout
        self.console.print(layout)

    def _get_fuel_color(self, fuel_price: int) -> str:
        """Get color for fuel price based on value.

        Args:
            fuel_price: Fuel price value

        Returns:
            Color string for Rich
        """
        if fuel_price < 550:
            return "green"
        elif fuel_price < 800:
            return "yellow"
        else:
            return "red"

    def _get_co2_color(self, co2_price: int) -> str:
        """Get color for CO2 price based on value.

        Args:
            co2_price: CO2 price value

        Returns:
            Color string for Rich
        """
        if co2_price < 130:
            return "green"
        elif co2_price < 150:
            return "yellow"
        else:
            return "red"

    def show_error(self, message: str) -> None:
        """Display an error message.

        Args:
            message: Error message to display
        """
        self.console.print(f"\n[bold red]Error:[/bold red] {message}\n")

    def show_loading(self) -> None:
        """Display loading message."""
        self.console.print("\n[cyan]Loading AM4 price data...[/cyan]\n")
