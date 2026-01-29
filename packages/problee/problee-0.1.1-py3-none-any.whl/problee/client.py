"""
Problee API Client

The main client class for interacting with the Problee API.
"""

import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests

from .api.markets import MarketsAPI
from .api.positions import PositionsAPI
from .api.quotes import QuotesAPI
from .streaming.sse import SSEClient
from .streaming.websocket import WebSocketClient
from .exceptions import (
    ProbError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    APIError,
)


class ProbClient:
    """
    Problee API Client.

    Example:
        ```python
        from problee import ProbClient

        # Initialize client
        client = ProbClient(api_key="pk_live_...")

        # List open markets
        markets = client.markets.list(status="open")
        for market in markets.markets:
            print(f"{market.question}: YES={market.prices.yes:.2%}")

        # Get a quote
        quote = client.quotes.get(
            market_id="0x...",
            side="buy",
            outcome="yes",
            amount="1000000000000000000"  # 1 USDC in wei
        )
        print(f"Price: {quote.price:.4f}, Shares: {quote.shares_out}")

        # Check positions
        positions = client.positions.list("0xYourWallet...")
        ```

    Attributes:
        markets: Markets API
        positions: Positions API
        quotes: Quotes API
        stream: SSE streaming client
        ws: WebSocket client
    """

    DEFAULT_BASE_URL = "https://api.problee.com"
    DEFAULT_TIMEOUT = 30

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
        builder_id: Optional[str] = None,
    ):
        """
        Initialize the Problee client.

        Args:
            api_key: API key (pk_live_... or pk_test_...)
            base_url: API base URL (defaults to https://api.problee.com)
            timeout: Request timeout in seconds
            max_retries: Max retries for failed requests
            builder_id: Optional builder ID for attribution
        """
        self._api_key = api_key
        self._base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._builder_id = builder_id

        # Initialize session
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "problee-python/0.1.0",
        })

        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

        if builder_id:
            self._session.headers["X-Builder-ID"] = builder_id

        # Initialize API modules
        self.markets = MarketsAPI(self)
        self.positions = PositionsAPI(self)
        self.quotes = QuotesAPI(self)

        # Initialize streaming clients (lazy)
        self._sse_client: Optional[SSEClient] = None
        self._ws_client: Optional[WebSocketClient] = None

    @property
    def stream(self) -> SSEClient:
        """Get SSE streaming client."""
        if self._sse_client is None:
            self._sse_client = SSEClient(self._base_url, self._api_key)
        return self._sse_client

    @property
    def ws(self) -> WebSocketClient:
        """Get WebSocket client."""
        if self._ws_client is None:
            self._ws_client = WebSocketClient(self._base_url, self._api_key)
        return self._ws_client

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an API request.

        Args:
            method: HTTP method
            path: API path
            params: Query parameters
            json: JSON body
            headers: Additional headers

        Returns:
            Response JSON

        Raises:
            AuthenticationError: Invalid API key
            RateLimitError: Rate limit exceeded
            NotFoundError: Resource not found
            ValidationError: Invalid request
            APIError: Other API errors
        """
        url = urljoin(self._base_url, path)
        request_headers = dict(self._session.headers)
        if headers:
            request_headers.update(headers)

        last_exception = None

        for attempt in range(self._max_retries):
            try:
                response = self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=request_headers,
                    timeout=self._timeout,
                )

                # Handle successful response
                if response.ok:
                    return response.json()

                # Handle errors
                self._handle_error(response)

            except requests.exceptions.Timeout:
                last_exception = APIError("Request timed out", code="TIMEOUT")
            except requests.exceptions.ConnectionError:
                last_exception = APIError("Connection failed", code="CONNECTION_ERROR")
            except ProbError:
                raise
            except Exception as e:
                last_exception = APIError(str(e))

            # Retry with backoff
            if attempt < self._max_retries - 1:
                time.sleep(2 ** attempt)

        if last_exception:
            raise last_exception
        raise APIError("Request failed after retries")

    def _handle_error(self, response: requests.Response) -> None:
        """Handle API error response."""
        status_code = response.status_code

        try:
            data = response.json()
            message = data.get("error", data.get("message", "Unknown error"))
            code = data.get("code")
        except Exception:
            message = response.text or "Unknown error"
            code = None

        if status_code == 401:
            raise AuthenticationError(message)
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif status_code == 404:
            raise NotFoundError(message)
        elif status_code == 400:
            errors = data.get("errors") if isinstance(data, dict) else None
            raise ValidationError(message, errors=errors)
        else:
            raise APIError(message, code=code, status_code=status_code)

    def get_rate_limit_info(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dict with rate limit headers from last request
        """
        # Make a lightweight request to get headers
        response = self._session.get(
            urljoin(self._base_url, "/healthz"),
            timeout=self._timeout,
        )
        return {
            "limit": response.headers.get("RateLimit-Limit"),
            "remaining": response.headers.get("RateLimit-Remaining"),
            "reset": response.headers.get("RateLimit-Reset"),
        }

    def close(self) -> None:
        """Close the client and clean up resources."""
        self._session.close()
        if self._sse_client:
            self._sse_client.close()

    def __enter__(self) -> "ProbClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
