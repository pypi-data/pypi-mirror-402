"""
Volare Signals API Client Library.

A Python client library for the Volare Signals API, providing
access to trading signals, upgrades, downgrades, and more.

Example:
    ```python
    from volare_signals import VolareSignalsClient

    # Create a client
    client = VolareSignalsClient(api_key="vk_your_api_key")

    # Get signal history
    response = client.get_history(date="2024-01-15", limit=100)
    for signal in response.data.signals:
        print(f"{signal.symbol}: {signal.rating} ({signal.side.value})")

    # Check rate limits
    print(f"Requests remaining: {response.rate_limit.remaining_minute}")
    ```

For async usage:
    ```python
    import asyncio
    from volare_signals import AsyncVolareSignalsClient

    async def main():
        async with AsyncVolareSignalsClient(api_key="vk_your_api_key") as client:
            response = await client.get_strong_buys(date="2024-01-15")
            print(f"Found {response.data.count} strong buy signals")

    asyncio.run(main())
    ```
"""

from volare_signals.client import (
    AsyncVolareSignalsClient,
    VolareSignalsClient,
)
from volare_signals.exceptions import (
    AuthenticationError,
    ForbiddenError,
    NetworkError,
    RateLimitExceededError,
    RetryExhaustedError,
    ServerError,
    ValidationError,
    VolareAPIError,
)
from volare_signals.models import (
    APIResponse,
    DowngradesResponse,
    ErrorResponse,
    NewSignalsResponse,
    PingResponse,
    RateLimitInfo,
    RatingBreakdown,
    RatingRange,
    Side,
    Signal,
    SignalHistoryResponse,
    StrongBuysResponse,
    StrongSellsResponse,
    SupportingAlgo,
    UpgradesResponse,
)
from volare_signals.retry import RetryConfig, RetryHandler, RetryState

__version__ = "1.0.0"
__author__ = "Volare Trading"
__email__ = "support@volaretrading.com"

__all__ = [
    "APIResponse",
    "AsyncVolareSignalsClient",
    "AuthenticationError",
    "DowngradesResponse",
    "ErrorResponse",
    "ForbiddenError",
    "NetworkError",
    "NewSignalsResponse",
    "PingResponse",
    "RateLimitExceededError",
    "RateLimitInfo",
    "RatingBreakdown",
    "RatingRange",
    "RetryConfig",
    "RetryExhaustedError",
    "RetryHandler",
    "RetryState",
    "ServerError",
    "Side",
    "Signal",
    "SignalHistoryResponse",
    "StrongBuysResponse",
    "StrongSellsResponse",
    "SupportingAlgo",
    "UpgradesResponse",
    "ValidationError",
    "VolareAPIError",
    "VolareSignalsClient",
    "__author__",
    "__email__",
    "__version__",
]
