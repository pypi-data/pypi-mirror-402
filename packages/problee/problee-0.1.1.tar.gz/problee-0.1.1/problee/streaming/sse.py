"""
SSE (Server-Sent Events) Client for real-time price updates
"""

import json
from typing import Iterator, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class SSEMessage:
    """SSE message."""
    event_type: str
    data: dict
    market_address: Optional[str] = None


class SSEClient:
    """
    SSE client for streaming price updates.

    Example:
        ```python
        client = ProbClient(api_key="pk_live_...")

        for update in client.stream.prices():
            print(f"Price update: {update.data}")
        ```
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._session = None

    def _get_session(self):
        """Get or create requests session."""
        if self._session is None:
            import requests
            self._session = requests.Session()
            if self._api_key:
                self._session.headers["Authorization"] = f"Bearer {self._api_key}"
        return self._session

    def prices(self, market_address: Optional[str] = None) -> Iterator[SSEMessage]:
        """
        Stream price updates.

        Args:
            market_address: Optional market address to filter updates

        Yields:
            SSEMessage objects with price data
        """
        params = {}
        if market_address:
            params["address"] = market_address

        session = self._get_session()
        url = f"{self._base_url}/api/prediction/market/stream"

        try:
            with session.get(url, params=params, stream=True) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if not line:
                        continue

                    line_str = line.decode("utf-8")
                    if line_str.startswith("data:"):
                        data_str = line_str[5:].strip()
                        if data_str:
                            try:
                                data = json.loads(data_str)
                                yield SSEMessage(
                                    event_type=data.get("type", "unknown"),
                                    data=data.get("payload", data),
                                    market_address=data.get("marketAddress"),
                                )
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            raise ConnectionError(f"SSE connection failed: {e}") from e

    def token_prices(self, symbol: str = "WLD") -> Iterator[SSEMessage]:
        """
        Stream token price updates.

        Args:
            symbol: Token symbol (default WLD)

        Yields:
            SSEMessage objects with token price data
        """
        for message in self.prices():
            if message.event_type == "tokenPrice":
                payload = message.data
                if payload.get("symbol") == symbol:
                    yield message

    def close(self):
        """Close the SSE connection."""
        if self._session:
            self._session.close()
            self._session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
