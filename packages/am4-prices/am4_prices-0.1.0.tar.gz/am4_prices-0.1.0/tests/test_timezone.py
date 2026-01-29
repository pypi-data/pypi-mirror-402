"""Tests for timezone handling."""

from datetime import datetime, timezone

import pytest

from am4_prices.models import DayPrices, PricePoint


class TestTimezoneHandling:
    """Tests to ensure UTC timezone is used correctly."""

    @pytest.fixture
    def sample_prices(self) -> list[PricePoint]:
        """Create sample price points with UTC timestamps."""
        return [
            PricePoint(time=f"{h:02d}:{m:02d}:00.000Z", fuel=500 + h * 10, co2=120 + h)
            for h in range(24)
            for m in [0, 30]
        ]

    def test_utc_time_matching(self, sample_prices: list[PricePoint]) -> None:
        """Test that UTC time correctly matches price timestamps."""
        day = DayPrices(day=1, prices=sample_prices)

        # Create a UTC time at 10:15 (should round to 10:00)
        utc_time = datetime(2026, 1, 20, 10, 15, tzinfo=timezone.utc)
        price = day.get_current_price(utc_time)

        # Should match the 10:00 slot
        assert price.time == "10:00:00.000Z"
        assert price.fuel == 600  # 500 + 10 * 10

    def test_utc_time_second_half(self, sample_prices: list[PricePoint]) -> None:
        """Test UTC time in second half of hour."""
        day = DayPrices(day=1, prices=sample_prices)

        # Create a UTC time at 14:45 (should round to 14:30)
        utc_time = datetime(2026, 1, 20, 14, 45, tzinfo=timezone.utc)
        price = day.get_current_price(utc_time)

        # Should match the 14:30 slot
        assert price.time == "14:30:00.000Z"
        assert price.fuel == 640  # 500 + 14 * 10

    def test_utc_upcoming_prices(self, sample_prices: list[PricePoint]) -> None:
        """Test that upcoming prices use UTC time correctly."""
        day = DayPrices(day=1, prices=sample_prices)

        # UTC time at 10:15 (rounds to 10:30 for next slot)
        utc_time = datetime(2026, 1, 20, 10, 15, tzinfo=timezone.utc)
        upcoming = day.get_upcoming_prices(utc_time, count=3)

        # Should get 10:30, 11:00, 11:30
        assert len(upcoming) == 3
        assert upcoming[0].time == "10:30:00.000Z"
        assert upcoming[1].time == "11:00:00.000Z"
        assert upcoming[2].time == "11:30:00.000Z"

    def test_timezone_aware_datetime(self, sample_prices: list[PricePoint]) -> None:
        """Test that timezone-aware datetime objects work correctly."""
        day = DayPrices(day=1, prices=sample_prices)

        # Create timezone-aware UTC datetime
        utc_aware = datetime.now(timezone.utc).replace(hour=15, minute=10)
        price = day.get_current_price(utc_aware)

        # Should match 15:00 slot
        assert price.time == "15:00:00.000Z"

    def test_midnight_utc(self, sample_prices: list[PricePoint]) -> None:
        """Test UTC midnight handling."""
        day = DayPrices(day=1, prices=sample_prices)

        # UTC midnight
        utc_midnight = datetime(2026, 1, 20, 0, 5, tzinfo=timezone.utc)
        price = day.get_current_price(utc_midnight)

        # Should match 00:00 slot
        assert price.time == "00:00:00.000Z"
        assert price.fuel == 500

    def test_end_of_day_utc(self, sample_prices: list[PricePoint]) -> None:
        """Test end of day UTC handling."""
        day = DayPrices(day=1, prices=sample_prices)

        # 23:45 UTC (should round to 23:30)
        utc_late = datetime(2026, 1, 20, 23, 45, tzinfo=timezone.utc)
        price = day.get_current_price(utc_late)

        # Should match 23:30 slot
        assert price.time == "23:30:00.000Z"

    def test_documentation_example(self, sample_prices: list[PricePoint]) -> None:
        """Test the example from documentation about timezone offset.

        If it's 10:00 AM EST (UTC-5), that's 15:00 UTC.
        The user should see prices for 15:00 UTC, not 10:00.
        """
        day = DayPrices(day=1, prices=sample_prices)

        # Simulate 10:00 AM EST = 15:00 UTC
        utc_time = datetime(2026, 1, 20, 15, 0, tzinfo=timezone.utc)
        price = day.get_current_price(utc_time)

        # Should show 15:00 UTC prices, not 10:00
        assert price.time == "15:00:00.000Z"
        assert price.fuel == 650  # 500 + 15 * 10

        # NOT the 10:00 prices
        assert price.fuel != 600  # Would be 500 + 10 * 10 if using local time

    def test_naive_datetime_interpreted_as_utc(self, sample_prices: list[PricePoint]) -> None:
        """Test that naive datetime (no timezone) is interpreted correctly.

        Our code uses datetime.now(timezone.utc) which creates timezone-aware
        datetimes, but we should handle both cases.
        """
        day = DayPrices(day=1, prices=sample_prices)

        # Naive datetime (no timezone info)
        naive_time = datetime(2026, 1, 20, 12, 15)
        price = day.get_current_price(naive_time)

        # Should still work and match 12:00 slot
        # (treating naive datetime as having the hours/minutes as-is)
        assert price.time == "12:00:00.000Z"
