"""
Quotes API
"""

from typing import Optional, TYPE_CHECKING
from ..models.quote import Quote, TransactionData

if TYPE_CHECKING:
    from ..client import ProbClient


class QuotesAPI:
    """Quotes API methods."""

    def __init__(self, client: "ProbClient"):
        self._client = client

    def get(
        self,
        market_id: str,
        side: str,
        outcome: str,
        amount: str,
        slippage_bps: int = 50,
    ) -> Quote:
        """
        Get a quote for a trade.

        Args:
            market_id: Market address
            side: "buy" or "sell"
            outcome: "yes", "no", or "draw"
            amount: Amount in wei (as string)
            slippage_bps: Slippage tolerance in basis points (default 50 = 0.5%)

        Returns:
            Quote object with price and execution details
        """
        payload = {
            "market_id": market_id,
            "side": side,
            "outcome": outcome,
            "amount": amount,
            "slippage_bps": slippage_bps,
        }
        response = self._client._request("POST", "/api/v1/quote", json=payload)
        return Quote.from_dict(response)

    def get_buy_yes(self, market_id: str, amount: str, **kwargs) -> Quote:
        """Get quote to buy YES shares."""
        return self.get(market_id, "buy", "yes", amount, **kwargs)

    def get_buy_no(self, market_id: str, amount: str, **kwargs) -> Quote:
        """Get quote to buy NO shares."""
        return self.get(market_id, "buy", "no", amount, **kwargs)

    def get_sell_yes(self, market_id: str, amount: str, **kwargs) -> Quote:
        """Get quote to sell YES shares."""
        return self.get(market_id, "sell", "yes", amount, **kwargs)

    def get_sell_no(self, market_id: str, amount: str, **kwargs) -> Quote:
        """Get quote to sell NO shares."""
        return self.get(market_id, "sell", "no", amount, **kwargs)

    def build_transaction(
        self,
        quote_id: str,
        rpc_url: str,
    ) -> TransactionData:
        """
        Build transaction data from a quote.

        Args:
            quote_id: Quote ID from get() response
            rpc_url: RPC URL for the chain

        Returns:
            TransactionData with calldata for execution
        """
        payload = {"quote_id": quote_id}
        headers = {"X-RPC-URL": rpc_url}
        response = self._client._request(
            "POST", "/api/v1/tx/build", json=payload, headers=headers
        )
        return TransactionData.from_dict(response)
