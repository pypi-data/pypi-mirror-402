"""
WebSocket Client for real-time market updates
"""

import json
import asyncio
from typing import Optional, AsyncIterator, Callable, Any, Set
from dataclasses import dataclass
from enum import Enum


class Channel(str, Enum):
    """WebSocket subscription channels."""
    MARKET = "market"
    TRADES = "trades"
    GLOBAL = "global"


@dataclass
class WebSocketMessage:
    """WebSocket message."""
    type: str
    data: dict
    market_id: Optional[str] = None
    timestamp: Optional[int] = None


class WebSocketClient:
    """
    WebSocket client for real-time market updates.

    Example:
        ```python
        import asyncio
        from problee import ProbClient

        async def main():
            client = ProbClient(api_key="pk_live_...")

            async with client.ws.connect() as ws:
                await ws.subscribe("market", "0x...")
                async for msg in ws:
                    print(f"Update: {msg.type} - {msg.data}")

        asyncio.run(main())
        ```
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._ws = None
        self._subscriptions: Set[str] = set()
        self._connected = False

    @property
    def ws_url(self) -> str:
        """Get WebSocket URL."""
        url = self._base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{url}/ws"
        if self._api_key:
            ws_url += f"?api_key={self._api_key}"
        return ws_url

    async def connect(self) -> "WebSocketClient":
        """
        Connect to WebSocket server.

        Returns:
            Self for use as async context manager
        """
        try:
            import websockets
        except ImportError:
            raise ImportError("websockets package required for WebSocket support. Install with: pip install websockets")

        self._ws = await websockets.connect(self.ws_url)
        self._connected = True

        # Wait for welcome message
        msg = await self._ws.recv()
        data = json.loads(msg)
        if data.get("type") != "subscribed":
            raise ConnectionError(f"Unexpected welcome message: {data}")

        return self

    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self._ws:
            await self._ws.close()
            self._ws = None
            self._connected = False
            self._subscriptions.clear()

    async def subscribe(
        self,
        channel: str,
        market_id: Optional[str] = None,
        events: Optional[list] = None,
    ):
        """
        Subscribe to a channel.

        Args:
            channel: Channel name (market, trades, global)
            market_id: Market address (required for market/trades channels)
            events: Optional list of event types to subscribe to
        """
        if not self._connected:
            raise ConnectionError("Not connected to WebSocket")

        message = {
            "type": "subscribe",
            "channel": channel,
        }
        if market_id:
            message["market_id"] = market_id
        if events:
            message["events"] = events

        await self._ws.send(json.dumps(message))

        # Wait for subscription confirmation
        response = await self._ws.recv()
        data = json.loads(response)

        if data.get("type") == "subscribed":
            sub_key = f"{channel}:{market_id}" if market_id else channel
            self._subscriptions.add(sub_key)
        elif data.get("type") == "error":
            raise Exception(f"Subscription failed: {data.get('error')}")

    async def unsubscribe(self, channel: str, market_id: Optional[str] = None):
        """
        Unsubscribe from a channel.

        Args:
            channel: Channel name
            market_id: Market address
        """
        if not self._connected:
            return

        message = {
            "type": "unsubscribe",
            "channel": channel,
        }
        if market_id:
            message["market_id"] = market_id

        await self._ws.send(json.dumps(message))

        sub_key = f"{channel}:{market_id}" if market_id else channel
        self._subscriptions.discard(sub_key)

    async def ping(self):
        """Send ping to keep connection alive."""
        if not self._connected:
            return
        await self._ws.send(json.dumps({"type": "ping"}))

    async def __aiter__(self) -> AsyncIterator[WebSocketMessage]:
        """Iterate over incoming messages."""
        if not self._connected:
            raise ConnectionError("Not connected to WebSocket")

        while self._connected:
            try:
                msg = await self._ws.recv()
                data = json.loads(msg)

                # Skip pong and subscription confirmations
                if data.get("type") in ("pong", "subscribed", "unsubscribed"):
                    continue

                yield WebSocketMessage(
                    type=data.get("type", "unknown"),
                    data=data,
                    market_id=data.get("market_id"),
                    timestamp=data.get("timestamp"),
                )
            except Exception:
                break

    async def __aenter__(self) -> "WebSocketClient":
        return await self.connect()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected

    def get_subscriptions(self) -> Set[str]:
        """Get current subscriptions."""
        return self._subscriptions.copy()
