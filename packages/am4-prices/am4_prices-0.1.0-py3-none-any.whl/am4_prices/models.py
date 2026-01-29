"""Data models for AM4 prices."""

from datetime import datetime

from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    """A single price measurement at a specific time."""

    time: str = Field(..., description="Time in HH:MM:SS.000Z format")
    fuel: int = Field(..., description="Fuel price", ge=0)
    co2: int = Field(..., description="CO2 price", ge=0)

    @property
    def hour(self) -> int:
        """Extract hour from time string."""
        return int(self.time.split(":")[0])

    @property
    def minute(self) -> int:
        """Extract minute from time string."""
        return int(self.time.split(":")[1])

    def __str__(self) -> str:
        """String representation."""
        return f"{self.time[:5]} - Fuel: ${self.fuel} | CO2: ${self.co2}"


class DayPrices(BaseModel):
    """Prices for a single day."""

    day: int = Field(..., description="Day number", ge=1)
    prices: list[PricePoint] = Field(..., description="List of price points")

    def get_current_price(self, current_time: datetime) -> PricePoint:
        """Get the price for the current time (30-min intervals)."""
        hour = current_time.hour
        minute = current_time.minute

        # Round to nearest 30-minute interval
        if minute >= 30:
            target_minute = 30
        else:
            target_minute = 0

        target_time = f"{hour:02d}:{target_minute:02d}:00.000Z"

        for price in self.prices:
            if price.time == target_time:
                return price

        # Fallback to first price if not found
        return self.prices[0]

    def get_upcoming_prices(self, current_time: datetime, count: int = 5) -> list[PricePoint]:
        """Get upcoming prices after current time."""
        hour = current_time.hour
        minute = current_time.minute

        # Round to next 30-minute interval
        if minute >= 30:
            if hour == 23:
                # Would go to next day
                return self.prices[:count]
            target_minute = 0
            target_hour = hour + 1
        else:
            target_minute = 30
            target_hour = hour

        upcoming = []
        found_start = False

        for price in self.prices:
            price_hour = price.hour
            price_minute = price.minute

            if not found_start:
                if price_hour > target_hour or (
                    price_hour == target_hour and price_minute >= target_minute
                ):
                    found_start = True
                    upcoming.append(price)
            else:
                upcoming.append(price)

            if len(upcoming) >= count:
                break

        # If we don't have enough, wrap around to start of day
        if len(upcoming) < count:
            remaining = count - len(upcoming)
            upcoming.extend(self.prices[:remaining])

        return upcoming


class PricesData(BaseModel):
    """Complete prices data structure."""

    days: dict[str, list[PricePoint]] = Field(..., description="Prices by day")

    def get_day(self, day: int) -> DayPrices:
        """Get prices for a specific day."""
        day_str = str(day)
        if day_str not in self.days:
            # Default to day 1 if not found
            day_str = "1"

        return DayPrices(day=day, prices=self.days[day_str])
