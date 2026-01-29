"""
Problee Python SDK

Official Python client for the Problee prediction market API.
"""

__version__ = "0.1.0"

from .client import ProbClient
from .models.market import Market, MarketStatus, MarketCategory
from .models.position import Position
from .models.quote import Quote
from .exceptions import (
    ProbError,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    ValidationError,
    APIError,
)

__all__ = [
    "ProbClient",
    "Market",
    "MarketStatus",
    "MarketCategory",
    "Position",
    "Quote",
    "ProbError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "APIError",
]
