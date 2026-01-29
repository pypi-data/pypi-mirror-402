"""API client for fetching AM4 price data."""

from typing import Optional

import httpx

from .models import PricesData


class AM4APIClient:
    """Client for fetching AM4 fuel and CO2 prices."""

    # Primary data source - GitHub raw URL
    DEFAULT_URL = (
        "https://raw.githubusercontent.com/theheuman/am4-helper/master/"
        "src/assets/resource-prices.json"
    )

    # Backup Firebase URL (if available)
    FIREBASE_URL = "https://am4-helper.web.app/tabs/prices"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        """Initialize the API client.

        Args:
            base_url: Custom base URL for the API
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or self.DEFAULT_URL
        self.timeout = timeout
        self._client = httpx.Client(timeout=self.timeout)

    def __enter__(self) -> "AM4APIClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def fetch_prices(self) -> PricesData:
        """Fetch current and upcoming price data.

        Returns:
            PricesData object containing all price information

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response cannot be parsed
        """
        try:
            response = self._client.get(self.base_url)
            response.raise_for_status()

            data = response.json()

            # Validate and parse the data
            return PricesData(days=data)

        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch prices from {self.base_url}: {e}") from e
        except (ValueError, KeyError) as e:
            raise ValueError(f"Failed to parse price data: {e}") from e

    async def fetch_prices_async(self) -> PricesData:
        """Async version of fetch_prices.

        Returns:
            PricesData object containing all price information

        Raises:
            httpx.HTTPError: If the request fails
            ValueError: If the response cannot be parsed
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.base_url)
                response.raise_for_status()

                data = response.json()

                # Validate and parse the data
                return PricesData(days=data)

            except httpx.HTTPError as e:
                raise httpx.HTTPError(f"Failed to fetch prices from {self.base_url}: {e}") from e
            except (ValueError, KeyError) as e:
                raise ValueError(f"Failed to parse price data: {e}") from e
