"""
Position data models
"""

from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Position:
    """User position in a market."""
    market_address: str
    yes_shares: str
    no_shares: str
    draw_shares: Optional[str] = None
    total_value_usd: Optional[float] = None
    unrealized_pnl: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        """Create Position from API response dict."""
        return cls(
            market_address=data["marketAddress"],
            yes_shares=data.get("yesShares", "0"),
            no_shares=data.get("noShares", "0"),
            draw_shares=data.get("drawShares"),
            total_value_usd=data.get("totalValueUsd"),
            unrealized_pnl=data.get("unrealizedPnl"),
        )

    def has_position(self) -> bool:
        """Check if user has any position."""
        yes = int(self.yes_shares) if self.yes_shares else 0
        no = int(self.no_shares) if self.no_shares else 0
        draw = int(self.draw_shares) if self.draw_shares else 0
        return yes > 0 or no > 0 or draw > 0


@dataclass
class PositionListResponse:
    """Response from list positions endpoint."""
    positions: List[Position]
    address: str

    @classmethod
    def from_dict(cls, data: dict) -> "PositionListResponse":
        positions = [Position.from_dict(p) for p in data.get("positions", [])]
        return cls(
            positions=positions,
            address=data.get("address", ""),
        )
