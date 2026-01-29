"""
Quote data models
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Quote:
    """Quote for a trade."""
    quote_id: str
    market_id: str
    side: str  # "buy" or "sell"
    outcome: str  # "yes", "no", or "draw"
    amount: str
    price: float
    shares_out: str
    price_impact: float
    fee: str
    expires_at: datetime
    slippage_bps: int = 50

    @classmethod
    def from_dict(cls, data: dict) -> "Quote":
        """Create Quote from API response dict."""
        return cls(
            quote_id=data["quoteId"],
            market_id=data["marketId"],
            side=data["side"],
            outcome=data["outcome"],
            amount=data["amount"],
            price=data["price"],
            shares_out=data["sharesOut"],
            price_impact=data.get("priceImpact", 0),
            fee=data.get("fee", "0"),
            expires_at=datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00")) if data.get("expiresAt") else datetime.now(),
            slippage_bps=data.get("slippageBps", 50),
        )

    def is_expired(self) -> bool:
        """Check if quote has expired."""
        return datetime.now(self.expires_at.tzinfo) > self.expires_at


@dataclass
class TransactionData:
    """Transaction data for executing a trade."""
    to: str
    data: str
    value: str
    gas_estimate: Optional[str] = None
    chain_id: int = 480  # World Chain

    @classmethod
    def from_dict(cls, data: dict) -> "TransactionData":
        """Create TransactionData from API response dict."""
        return cls(
            to=data["to"],
            data=data["data"],
            value=data.get("value", "0"),
            gas_estimate=data.get("gasEstimate"),
            chain_id=data.get("chainId", 480),
        )
