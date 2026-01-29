"""
Positions API
"""

from typing import Optional, TYPE_CHECKING
from ..models.position import Position, PositionListResponse

if TYPE_CHECKING:
    from ..client import ProbClient


class PositionsAPI:
    """Positions API methods."""

    def __init__(self, client: "ProbClient"):
        self._client = client

    def list(self, address: str) -> PositionListResponse:
        """
        Get all positions for a wallet address.

        Args:
            address: Wallet address (0x...)

        Returns:
            PositionListResponse with list of positions
        """
        response = self._client._request("GET", f"/api/v1/positions/{address}")
        return PositionListResponse.from_dict(response)

    def get(self, address: str, market_id: str) -> Optional[Position]:
        """
        Get position for a specific market.

        Args:
            address: Wallet address
            market_id: Market address

        Returns:
            Position or None if no position
        """
        params = {"market_id": market_id}
        response = self._client._request(
            "GET", f"/api/v1/positions/{address}", params=params
        )
        positions = response.get("positions", [])
        if positions:
            return Position.from_dict(positions[0])
        return None
