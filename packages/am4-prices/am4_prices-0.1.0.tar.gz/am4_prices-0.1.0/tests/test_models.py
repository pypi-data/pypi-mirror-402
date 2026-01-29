"""Tests for data models."""

from datetime import datetime

import pytest

from am4_prices.models import DayPrices, PricePoint, PricesData


class TestPricePoint:
    """Tests for PricePoint model."""

    def test_price_point_creation(self) -> None:
        """Test creating a PricePoint."""
        point = PricePoint(time="10:30:00.000Z", fuel=650, co2=140)
        assert point.time == "10:30:00.000Z"
        assert point.fuel == 650
        assert point.co2 == 140

    def test_hour_property(self) -> None:
        """Test hour extraction."""
        point = PricePoint(time="15:30:00.000Z", fuel=650, co2=140)
        assert point.hour == 15

    def test_minute_property(self) -> None:
        """Test minute extraction."""
        point = PricePoint(time="15:30:00.000Z", fuel=650, co2=140)
        assert point.minute == 30

    def test_string_representation(self) -> None:
        """Test string representation."""
        point = PricePoint(time="10:30:00.000Z", fuel=650, co2=140)
        result = str(point)
        assert "10:30" in result
        assert "650" in result
        assert "140" in result


class TestDayPrices:
    """Tests for DayPrices model."""

    @pytest.fixture
    def sample_prices(self) -> list[PricePoint]:
        """Create sample price points."""
        return [
            PricePoint(time=f"{h:02d}:{m:02d}:00.000Z", fuel=500 + h * 10, co2=120 + h)
            for h in range(24)
            for m in [0, 30]
        ]

    def test_day_prices_creation(self, sample_prices: list[PricePoint]) -> None:
        """Test creating DayPrices."""
        day = DayPrices(day=1, prices=sample_prices)
        assert day.day == 1
        assert len(day.prices) == 48

    def test_get_current_price_first_half_hour(self, sample_prices: list[PricePoint]) -> None:
        """Test getting current price in first half of hour."""
        day = DayPrices(day=1, prices=sample_prices)
        current_time = datetime(2026, 1, 20, 10, 15)
        price = day.get_current_price(current_time)
        assert price.time == "10:00:00.000Z"

    def test_get_current_price_second_half_hour(self, sample_prices: list[PricePoint]) -> None:
        """Test getting current price in second half of hour."""
        day = DayPrices(day=1, prices=sample_prices)
        current_time = datetime(2026, 1, 20, 10, 45)
        price = day.get_current_price(current_time)
        assert price.time == "10:30:00.000Z"

    def test_get_upcoming_prices(self, sample_prices: list[PricePoint]) -> None:
        """Test getting upcoming prices."""
        day = DayPrices(day=1, prices=sample_prices)
        current_time = datetime(2026, 1, 20, 10, 15)
        upcoming = day.get_upcoming_prices(current_time, count=5)
        assert len(upcoming) == 5
        assert upcoming[0].time == "10:30:00.000Z"


class TestPricesData:
    """Tests for PricesData model."""

    @pytest.fixture
    def sample_data(self) -> dict[str, list[dict[str, object]]]:
        """Create sample prices data."""
        return {
            "1": [
                {"time": "00:00:00.000Z", "fuel": 500, "co2": 120},
                {"time": "00:30:00.000Z", "fuel": 510, "co2": 125},
            ],
            "2": [
                {"time": "00:00:00.000Z", "fuel": 520, "co2": 130},
                {"time": "00:30:00.000Z", "fuel": 530, "co2": 135},
            ],
        }

    def test_prices_data_creation(self, sample_data: dict[str, list[dict[str, object]]]) -> None:
        """Test creating PricesData."""
        data = PricesData(days=sample_data)
        assert "1" in data.days
        assert "2" in data.days

    def test_get_day(self, sample_data: dict[str, list[dict[str, object]]]) -> None:
        """Test getting prices for a specific day."""
        data = PricesData(days=sample_data)
        day = data.get_day(1)
        assert day.day == 1
        assert len(day.prices) == 2

    def test_get_nonexistent_day(self, sample_data: dict[str, list[dict[str, object]]]) -> None:
        """Test getting prices for non-existent day defaults to day 1."""
        data = PricesData(days=sample_data)
        day = data.get_day(99)
        assert day.day == 99
        assert len(day.prices) == 2  # Falls back to day 1 data
