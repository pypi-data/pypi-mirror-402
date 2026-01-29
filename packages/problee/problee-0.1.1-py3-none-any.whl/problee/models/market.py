"""
Market data models
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


class MarketStatus(str, Enum):
    """Market status enum."""
    OPEN = "open"
    CLOSED = "closed"
    RESOLVED = "resolved"
    PENDING = "pending"
    LIVE = "live"


class MarketCategory(str, Enum):
    """Market category enum."""
    SPORTS = "sports"
    POLITICS = "politics"
    CRYPTO = "crypto"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"


@dataclass
class MarketPrices:
    """Market outcome prices."""
    yes: float
    no: float
    draw: Optional[float] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MarketPrices":
        return cls(
            yes=data.get("yes", 0),
            no=data.get("no", 0),
            draw=data.get("draw"),
        )


@dataclass
class Market:
    """Prediction market data model."""
    address: str
    question: str
    status: MarketStatus
    category: MarketCategory
    prices: MarketPrices
    volume_24h: str
    liquidity: str
    created_at: datetime
    close_time: datetime
    resolution_time: Optional[datetime] = None
    outcome: Optional[int] = None
    market_type: str = "BINARY"
    outcome_1_label: str = "YES"
    outcome_2_label: str = "NO"
    outcome_3_label: Optional[str] = None
    image_url: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Market":
        """Create Market from API response dict."""
        prices_data = data.get("prices", {})
        if isinstance(prices_data, dict):
            prices = MarketPrices.from_dict(prices_data)
        else:
            prices = MarketPrices(yes=0, no=0)

        return cls(
            address=data["address"],
            question=data["question"],
            status=MarketStatus(data.get("status", "open")),
            category=MarketCategory(data.get("category", "other")),
            prices=prices,
            volume_24h=data.get("volume24h", "0"),
            liquidity=data.get("liquidity", "0"),
            created_at=datetime.fromisoformat(data["createdAt"].replace("Z", "+00:00")) if data.get("createdAt") else datetime.now(),
            close_time=datetime.fromisoformat(data["closeTime"].replace("Z", "+00:00")) if data.get("closeTime") else datetime.now(),
            resolution_time=datetime.fromisoformat(data["resolutionTime"].replace("Z", "+00:00")) if data.get("resolutionTime") else None,
            outcome=data.get("outcome"),
            market_type=data.get("marketType", "BINARY"),
            outcome_1_label=data.get("outcome1Label", "YES"),
            outcome_2_label=data.get("outcome2Label", "NO"),
            outcome_3_label=data.get("outcome3Label"),
            image_url=data.get("imageUrl"),
        )

    def is_open(self) -> bool:
        """Check if market is open for trading."""
        return self.status in (MarketStatus.OPEN, MarketStatus.LIVE, MarketStatus.PENDING)

    def is_resolved(self) -> bool:
        """Check if market is resolved."""
        return self.status == MarketStatus.RESOLVED


@dataclass
class MarketListResponse:
    """Response from list markets endpoint."""
    markets: List[Market]
    next_cursor: Optional[str] = None
    total: Optional[int] = None

    @classmethod
    def from_dict(cls, data: dict) -> "MarketListResponse":
        markets = [Market.from_dict(m) for m in data.get("markets", [])]
        return cls(
            markets=markets,
            next_cursor=data.get("nextCursor"),
            total=data.get("total"),
        )
