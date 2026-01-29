"""Tests for the ProbClient."""

import pytest
import responses
from problee import ProbClient
from problee.exceptions import AuthenticationError, NotFoundError, RateLimitError


class TestProbClient:
    """Test ProbClient."""

    def test_client_init(self):
        """Test client initialization."""
        client = ProbClient(api_key="pk_test_123")
        assert client._api_key == "pk_test_123"
        assert client._base_url == "https://api.problee.com"

    def test_client_custom_base_url(self):
        """Test client with custom base URL."""
        client = ProbClient(base_url="https://sandbox-api.problee.com")
        assert client._base_url == "https://sandbox-api.problee.com"

    def test_client_builder_id(self):
        """Test client with builder ID."""
        client = ProbClient(builder_id="my-app")
        assert client._session.headers.get("X-Builder-ID") == "my-app"

    @responses.activate
    def test_list_markets(self):
        """Test listing markets."""
        responses.add(
            responses.GET,
            "https://api.problee.com/api/v1/markets",
            json={
                "markets": [
                    {
                        "address": "0x123",
                        "question": "Test Market?",
                        "status": "open",
                        "category": "crypto",
                        "prices": {"yes": 0.5, "no": 0.5},
                        "volume24h": "1000",
                        "liquidity": "10000",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "closeTime": "2024-12-31T23:59:59Z",
                    }
                ],
                "nextCursor": None,
            },
            status=200,
        )

        client = ProbClient(api_key="pk_test_123")
        result = client.markets.list()

        assert len(result.markets) == 1
        assert result.markets[0].address == "0x123"
        assert result.markets[0].question == "Test Market?"
        assert result.markets[0].prices.yes == 0.5

    @responses.activate
    def test_get_market(self):
        """Test getting a single market."""
        responses.add(
            responses.GET,
            "https://api.problee.com/api/v1/markets/0x123",
            json={
                "address": "0x123",
                "question": "Test Market?",
                "status": "open",
                "category": "crypto",
                "prices": {"yes": 0.6, "no": 0.4},
                "volume24h": "1000",
                "liquidity": "10000",
                "createdAt": "2024-01-01T00:00:00Z",
                "closeTime": "2024-12-31T23:59:59Z",
            },
            status=200,
        )

        client = ProbClient(api_key="pk_test_123")
        market = client.markets.get("0x123")

        assert market.address == "0x123"
        assert market.prices.yes == 0.6
        assert market.prices.no == 0.4

    @responses.activate
    def test_get_quote(self):
        """Test getting a quote."""
        responses.add(
            responses.POST,
            "https://api.problee.com/api/v1/quote",
            json={
                "quoteId": "quote-123",
                "marketId": "0x123",
                "side": "buy",
                "outcome": "yes",
                "amount": "1000000000000000000",
                "price": 0.55,
                "sharesOut": "1800000000000000000",
                "priceImpact": 0.01,
                "fee": "10000000000000000",
                "expiresAt": "2024-01-01T00:01:00Z",
                "slippageBps": 50,
            },
            status=200,
        )

        client = ProbClient(api_key="pk_test_123")
        quote = client.quotes.get(
            market_id="0x123",
            side="buy",
            outcome="yes",
            amount="1000000000000000000",
        )

        assert quote.quote_id == "quote-123"
        assert quote.price == 0.55
        assert quote.shares_out == "1800000000000000000"

    @responses.activate
    def test_authentication_error(self):
        """Test handling authentication error."""
        responses.add(
            responses.GET,
            "https://api.problee.com/api/v1/markets",
            json={"error": "Invalid API key"},
            status=401,
        )

        client = ProbClient(api_key="invalid")
        with pytest.raises(AuthenticationError):
            client.markets.list()

    @responses.activate
    def test_not_found_error(self):
        """Test handling not found error."""
        responses.add(
            responses.GET,
            "https://api.problee.com/api/v1/markets/0xinvalid",
            json={"error": "Market not found"},
            status=404,
        )

        client = ProbClient(api_key="pk_test_123")
        with pytest.raises(NotFoundError):
            client.markets.get("0xinvalid")

    @responses.activate
    def test_rate_limit_error(self):
        """Test handling rate limit error."""
        responses.add(
            responses.GET,
            "https://api.problee.com/api/v1/markets",
            json={"error": "Rate limit exceeded"},
            status=429,
            headers={"Retry-After": "60"},
        )

        client = ProbClient(api_key="pk_test_123")
        with pytest.raises(RateLimitError) as exc_info:
            client.markets.list()

        assert exc_info.value.retry_after == 60


class TestModels:
    """Test data models."""

    def test_market_from_dict(self):
        """Test creating Market from dict."""
        from problee.models.market import Market

        data = {
            "address": "0x123",
            "question": "Test?",
            "status": "open",
            "category": "crypto",
            "prices": {"yes": 0.5, "no": 0.5},
            "volume24h": "1000",
            "liquidity": "10000",
            "createdAt": "2024-01-01T00:00:00Z",
            "closeTime": "2024-12-31T23:59:59Z",
        }

        market = Market.from_dict(data)
        assert market.address == "0x123"
        assert market.is_open()
        assert not market.is_resolved()

    def test_position_from_dict(self):
        """Test creating Position from dict."""
        from problee.models.position import Position

        data = {
            "marketAddress": "0x123",
            "yesShares": "1000000000000000000",
            "noShares": "0",
        }

        position = Position.from_dict(data)
        assert position.market_address == "0x123"
        assert position.has_position()

    def test_quote_from_dict(self):
        """Test creating Quote from dict."""
        from problee.models.quote import Quote

        data = {
            "quoteId": "quote-123",
            "marketId": "0x123",
            "side": "buy",
            "outcome": "yes",
            "amount": "1000000000000000000",
            "price": 0.55,
            "sharesOut": "1800000000000000000",
            "expiresAt": "2024-01-01T00:01:00Z",
        }

        quote = Quote.from_dict(data)
        assert quote.quote_id == "quote-123"
        assert quote.price == 0.55
