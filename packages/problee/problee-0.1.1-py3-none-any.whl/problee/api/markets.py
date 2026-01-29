"""
Markets API
"""

from typing import Optional, List, TYPE_CHECKING
from ..models.market import Market, MarketListResponse, MarketStatus, MarketCategory

if TYPE_CHECKING:
    from ..client import ProbClient


class MarketsAPI:
    """Markets API methods."""

    def __init__(self, client: "ProbClient"):
        self._client = client

    def list(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        sort: Optional[str] = None,
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> MarketListResponse:
        """
        List markets with optional filters.

        Args:
            status: Filter by status (open, closed, resolved)
            category: Filter by category (sports, politics, crypto, entertainment, other)
            sort: Sort order (new, trending, volume_24h, closing_soon)
            limit: Max results per page (default 20, max 100)
            cursor: Pagination cursor

        Returns:
            MarketListResponse with list of markets and pagination info
        """
        params = {"limit": limit}
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if sort:
            params["sort"] = sort
        if cursor:
            params["cursor"] = cursor

        response = self._client._request("GET", "/api/v1/markets", params=params)
        return MarketListResponse.from_dict(response)

    def get(self, market_id: str) -> Market:
        """
        Get a single market by ID (address).

        Args:
            market_id: Market address

        Returns:
            Market object
        """
        response = self._client._request("GET", f"/api/v1/markets/{market_id}")
        return Market.from_dict(response)

    def get_history(
        self,
        market_id: str,
        interval: str = "1h",
        limit: int = 100,
    ) -> List[dict]:
        """
        Get price history for a market.

        Args:
            market_id: Market address
            interval: Time bucket (1m, 5m, 1h, 1d)
            limit: Max data points

        Returns:
            List of price history points
        """
        params = {"interval": interval, "limit": limit}
        response = self._client._request(
            "GET", f"/api/v1/markets/{market_id}/history", params=params
        )
        return response.get("history", [])

    def get_trades(
        self,
        market_id: str,
        limit: int = 50,
    ) -> List[dict]:
        """
        Get recent trades for a market.

        Args:
            market_id: Market address
            limit: Max trades to return

        Returns:
            List of trade objects
        """
        params = {"limit": limit}
        response = self._client._request(
            "GET", f"/api/v1/markets/{market_id}/trades", params=params
        )
        return response.get("trades", [])

    def list_open(self, **kwargs) -> MarketListResponse:
        """List open markets."""
        return self.list(status="open", **kwargs)

    def list_resolved(self, **kwargs) -> MarketListResponse:
        """List resolved markets."""
        return self.list(status="resolved", **kwargs)

    def list_by_category(self, category: str, **kwargs) -> MarketListResponse:
        """List markets by category."""
        return self.list(category=category, **kwargs)
