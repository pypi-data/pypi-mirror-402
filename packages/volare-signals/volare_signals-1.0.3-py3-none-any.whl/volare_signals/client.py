"""
Volare Signals API Client.

This module provides the main client class for interacting with the
Volare Signals API. It handles authentication, request execution,
error handling, and response parsing.
"""

from __future__ import annotations

import logging
from datetime import date as date_type
from typing import Any, TypeVar
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from volare_signals.exceptions import (
    NetworkError,
    RateLimitExceededError,
    VolareAPIError,
)
from volare_signals.models import (
    APIResponse,
    DowngradesResponse,
    ErrorResponse,
    LatestSignalsResponse,
    NewSignalsResponse,
    PingResponse,
    RateLimitInfo,
    SignalHistoryResponse,
    StrongBuysResponse,
    StrongSellsResponse,
    UpgradesResponse,
)
from volare_signals.retry import RetryConfig, RetryHandler

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

DEFAULT_BASE_URL = "https://api.volaretrading.com"
DEFAULT_TIMEOUT = 30.0
API_KEY_HEADER = "X-Api-Key"
API_KEY_PREFIX = "vk_"


class VolareSignalsClient:
    """
    Client for the Volare Signals API.

    This client provides methods for all Volare Signals API endpoints
    with built-in authentication, error handling, and retry logic.

    Example:
        ```python
        from volare_signals import VolareSignalsClient

        client = VolareSignalsClient(api_key="vk_your_api_key")

        # Get signal history
        response = client.get_history(date="2024-01-15", limit=100)
        for signal in response.data.signals:
            print(f"{signal.symbol}: {signal.rating}")

        # Check rate limits
        print(f"Remaining: {response.rate_limit.remaining_minute}")
        ```

    Attributes:
        base_url: The base URL for API requests.
        api_key: The API key used for authentication.
        timeout: Request timeout in seconds.
        last_rate_limit: Rate limit info from the most recent request.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: RetryConfig | None = None,
        http_client: httpx.Client | None = None,
    ) -> None:
        """
        Initialize the Volare Signals API client.

        Args:
            api_key: Your Volare API key (format: vk_...).
            base_url: Base URL for the API. Override for testing or
                     custom deployments.
            timeout: Request timeout in seconds.
            retry_config: Configuration for retry behavior.
            http_client: Optional pre-configured httpx client.

        Raises:
            ValueError: If the API key format is invalid.
        """
        self._validate_api_key(api_key)

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.last_rate_limit: RateLimitInfo | None = None

        self._client = http_client or httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._default_headers(),
        )
        self._retry_handler = RetryHandler(self.retry_config)
        self._owns_client = http_client is None

    def _validate_api_key(self, api_key: str) -> None:
        """Validate API key format."""
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith(API_KEY_PREFIX):
            raise ValueError(f"API key must start with '{API_KEY_PREFIX}'. Got: {api_key[:10]}...")

    def _default_headers(self) -> dict[str, str]:
        """Get default headers for all requests."""
        return {
            API_KEY_HEADER: self.api_key,
            "Accept": "application/json",
            "User-Agent": "volare-signals-python/1.0.0",
        }

    def _build_url(self, path: str) -> str:
        """Build full URL from path."""
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _parse_rate_limit(self, response: httpx.Response) -> RateLimitInfo:
        """Parse rate limit information from response headers."""
        headers = dict(response.headers)
        return RateLimitInfo.from_headers(headers)

    def _handle_error_response(
        self,
        response: httpx.Response,
        rate_limit: RateLimitInfo,
    ) -> None:
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            error_response = ErrorResponse.model_validate(error_data)
        except Exception:
            error_response = ErrorResponse(
                error="UNKNOWN_ERROR",
                message=response.text or f"HTTP {response.status_code}",
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitExceededError(
                message=error_response.message,
                error_code=error_response.error,
                details=error_response.details,
                rate_limit=rate_limit,
                retry_after=int(retry_after) if retry_after else None,
            )

        raise VolareAPIError.from_response(
            error_response,
            response.status_code,
            rate_limit,
        )

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API endpoint path.
            params: Query parameters.

        Returns:
            The HTTP response.

        Raises:
            NetworkError: If a connection error occurs.
            VolareAPIError: If the API returns an error response.
        """
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}

        def make_request() -> httpx.Response:
            try:
                response = self._client.request(
                    method=method,
                    url=path,
                    params=filtered_params,
                )
            except httpx.ConnectError as e:
                raise NetworkError(f"Failed to connect to {self.base_url}", e)
            except httpx.TimeoutException as e:
                raise NetworkError(f"Request timed out after {self.timeout}s", e)
            except httpx.HTTPError as e:
                raise NetworkError(f"HTTP error occurred: {e}", e)

            rate_limit = self._parse_rate_limit(response)
            self.last_rate_limit = rate_limit

            if not response.is_success:
                self._handle_error_response(response, rate_limit)

            return response

        return self._retry_handler.execute(make_request)

    def _get(
        self,
        path: str,
        response_type: type[T],
        params: dict[str, Any] | None = None,
    ) -> APIResponse[T]:
        """
        Make a GET request and parse the response.

        Args:
            path: API endpoint path.
            response_type: Pydantic model class for response parsing.
            params: Query parameters.

        Returns:
            Parsed response with rate limit info.
        """
        response = self._request("GET", path, params)
        rate_limit = self._parse_rate_limit(response)

        data = response_type.model_validate(response.json())
        return APIResponse(
            data=data,
            rate_limit=rate_limit,
            status_code=response.status_code,
        )

    def ping(self) -> APIResponse[PingResponse]:
        """
        Check API connectivity and service status.

        Returns:
            APIResponse containing PingResponse with service status.

        Raises:
            AuthenticationError: If API key is invalid.
            NetworkError: If unable to connect to the API.

        Example:
            ```python
            response = client.ping()
            print(f"API status: {response.data.status}")
            ```
        """
        return self._get("/ping", PingResponse)

    def get_rate_limit_status(self) -> RateLimitInfo:
        """
        Get current rate limit status.

        Makes a lightweight ping request to retrieve current rate limit
        information without fetching actual data.

        Returns:
            RateLimitInfo with current rate limit status.

        Raises:
            AuthenticationError: If API key is invalid.
            NetworkError: If unable to connect to the API.

        Example:
            ```python
            rate_limit = client.get_rate_limit_status()
            print(f"Requests remaining this minute: {rate_limit.remaining_minute}")
            print(f"Requests remaining today: {rate_limit.remaining_day}")

            if rate_limit.is_minute_exhausted:
                print("Wait for minute limit to reset")
            ```
        """
        response = self.ping()
        return response.rate_limit

    def get_latest(
        self,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> APIResponse[LatestSignalsResponse]:
        """
        Get the most recent signals.

        Retrieves signals from the latest date with available signals.
        This is the quickest way to get current signal data.

        Args:
            min_rating: Minimum signal rating filter (1-10).
            max_rating: Maximum signal rating filter (1-10).

        Returns:
            APIResponse containing LatestSignalsResponse with signals.

        Raises:
            ValidationError: If parameters are invalid.
            AuthenticationError: If API key is invalid.
            RateLimitExceededError: If rate limit is exceeded.

        Example:
            ```python
            response = client.get_latest(min_rating=7)
            print(f"Latest signals from {response.data.date}")
            for signal in response.data.signals:
                print(f"{signal.symbol}: {signal.rating}")
            ```
        """
        if min_rating is not None and not 1 <= min_rating <= 10:
            raise ValueError("min_rating must be between 1 and 10")
        if max_rating is not None and not 1 <= max_rating <= 10:
            raise ValueError("max_rating must be between 1 and 10")

        return self._get(
            "/signals/latest",
            LatestSignalsResponse,
            params={
                "min_rating": min_rating,
                "max_rating": max_rating,
            },
        )

    def get_history(
        self,
        start_date: str | date_type,
        end_date: str | date_type,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> APIResponse[SignalHistoryResponse]:
        """
        Get historical signals for a date range.

        Retrieves all signals generated within the specified date range,
        optionally filtered by rating range.

        Args:
            start_date: Start date (YYYY-MM-DD string or date object, inclusive).
            end_date: End date (YYYY-MM-DD string or date object, inclusive).
            min_rating: Minimum signal rating (1-10).
            max_rating: Maximum signal rating (1-10).

        Returns:
            APIResponse containing SignalHistoryResponse with signals.

        Raises:
            ValidationError: If parameters are invalid.
            AuthenticationError: If API key is invalid.
            RateLimitExceededError: If rate limit is exceeded.

        Note:
            Maximum date range is 90 days.

        Example:
            ```python
            response = client.get_history(
                start_date="2024-01-01",
                end_date="2024-01-15",
                min_rating=7
            )
            print(f"Found {response.data.count} signals")
            ```
        """
        if min_rating is not None and not 1 <= min_rating <= 10:
            raise ValueError("min_rating must be between 1 and 10")
        if max_rating is not None and not 1 <= max_rating <= 10:
            raise ValueError("max_rating must be between 1 and 10")

        start_date_str = start_date.isoformat() if isinstance(start_date, date_type) else start_date
        end_date_str = end_date.isoformat() if isinstance(end_date, date_type) else end_date

        return self._get(
            "/signals/history",
            SignalHistoryResponse,
            params={
                "start_date": start_date_str,
                "end_date": end_date_str,
                "min_rating": min_rating,
                "max_rating": max_rating,
            },
        )

    def get_strong_buys(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[StrongBuysResponse]:
        """
        Get strong buy signals for a given date.

        Retrieves signals with high ratings (typically 8-10) that indicate
        strong bullish sentiment.

        Args:
            date: Date to query (YYYY-MM-DD string or date object).
            limit: Maximum number of signals to return.

        Returns:
            APIResponse containing StrongBuysResponse with signals.

        Example:
            ```python
            response = client.get_strong_buys(date="2024-01-15")
            for signal in response.data.signals:
                if signal.side.value == "long":
                    print(f"Strong buy: {signal.symbol}")
            ```
        """
        date_str = date.isoformat() if isinstance(date, date_type) else date

        return self._get(
            "/signals/strong-buys",
            StrongBuysResponse,
            params={"date": date_str, "limit": limit},
        )

    def get_strong_sells(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[StrongSellsResponse]:
        """
        Get strong sell signals for a given date.

        Retrieves signals with low ratings (typically 1-3) that indicate
        strong bearish sentiment.

        Args:
            date: Date to query (YYYY-MM-DD string or date object).
            limit: Maximum number of signals to return.

        Returns:
            APIResponse containing StrongSellsResponse with signals.

        Example:
            ```python
            response = client.get_strong_sells(date="2024-01-15")
            for signal in response.data.signals:
                print(f"Strong sell: {signal.symbol} (rating: {signal.rating})")
            ```
        """
        date_str = date.isoformat() if isinstance(date, date_type) else date

        return self._get(
            "/signals/strong-sells",
            StrongSellsResponse,
            params={"date": date_str, "limit": limit},
        )

    def get_upgrades(
        self,
        date: str | date_type | None = None,
        min_change: int | None = None,
        limit: int | None = None,
    ) -> APIResponse[UpgradesResponse]:
        """
        Get signals that were upgraded from a previous rating.

        Retrieves signals where the rating increased compared to the
        previous period.

        Args:
            date: Date to query (YYYY-MM-DD string or date object).
            min_change: Minimum positive rating change to include.
            limit: Maximum number of signals to return.

        Returns:
            APIResponse containing UpgradesResponse with signals.

        Example:
            ```python
            # Get signals upgraded by at least 3 points
            response = client.get_upgrades(
                date="2024-01-15",
                min_change=3
            )
            for signal in response.data.signals:
                print(f"{signal.symbol}: {signal.previous_rating} -> {signal.rating}")
            ```
        """
        if min_change is not None and min_change < 1:
            raise ValueError("min_change must be a positive integer")

        date_str = date.isoformat() if isinstance(date, date_type) else date

        return self._get(
            "/signals/upgrades",
            UpgradesResponse,
            params={"date": date_str, "min_change": min_change, "limit": limit},
        )

    def get_downgrades(
        self,
        date: str | date_type | None = None,
        max_change: int | None = None,
        limit: int | None = None,
    ) -> APIResponse[DowngradesResponse]:
        """
        Get signals that were downgraded from a previous rating.

        Retrieves signals where the rating decreased compared to the
        previous period.

        Args:
            date: Date to query (YYYY-MM-DD string or date object).
            max_change: Maximum (most negative) rating change to include.
                       Must be negative (e.g., -2 for downgrades of 2+ points).
            limit: Maximum number of signals to return.

        Returns:
            APIResponse containing DowngradesResponse with signals.

        Example:
            ```python
            # Get signals downgraded by at least 2 points
            response = client.get_downgrades(
                date="2024-01-15",
                max_change=-2
            )
            for signal in response.data.signals:
                change = signal.rating_change
                print(f"{signal.symbol}: downgraded by {abs(change)} points")
            ```
        """
        if max_change is not None and max_change >= 0:
            raise ValueError("max_change must be a negative integer")

        date_str = date.isoformat() if isinstance(date, date_type) else date

        return self._get(
            "/signals/downgrades",
            DowngradesResponse,
            params={"date": date_str, "max_change": max_change, "limit": limit},
        )

    def get_new_signals(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[NewSignalsResponse]:
        """
        Get newly generated signals for a given date.

        Retrieves signals for instruments that didn't have a signal in
        the previous period (previous_rating is null).

        Args:
            date: Date to query (YYYY-MM-DD string or date object).
            limit: Maximum number of signals to return.

        Returns:
            APIResponse containing NewSignalsResponse with signals.

        Example:
            ```python
            response = client.get_new_signals(date="2024-01-15")
            print(f"Found {response.data.count} new signals")
            for signal in response.data.signals:
                print(f"New signal: {signal.symbol} ({signal.side.value})")
            ```
        """
        date_str = date.isoformat() if isinstance(date, date_type) else date

        return self._get(
            "/signals/new",
            NewSignalsResponse,
            params={"date": date_str, "limit": limit},
        )

    def close(self) -> None:
        """
        Close the HTTP client and release resources.

        This should be called when you're done using the client to
        properly close connections. Alternatively, use the client
        as a context manager.
        """
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> VolareSignalsClient:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and close client."""
        self.close()

    def __repr__(self) -> str:
        return f"VolareSignalsClient(base_url={self.base_url!r}, api_key={self.api_key[:8]}...)"


class AsyncVolareSignalsClient:
    """
    Async client for the Volare Signals API.

    This client provides async methods for all Volare Signals API endpoints.
    Use this client when working with asyncio-based applications.

    Example:
        ```python
        import asyncio
        from volare_signals import AsyncVolareSignalsClient

        async def main():
            async with AsyncVolareSignalsClient(api_key="vk_your_key") as client:
                response = await client.get_history(date="2024-01-15")
                for signal in response.data.signals:
                    print(f"{signal.symbol}: {signal.rating}")

        asyncio.run(main())
        ```
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        retry_config: RetryConfig | None = None,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Initialize the async Volare Signals API client.

        Args:
            api_key: Your Volare API key (format: vk_...).
            base_url: Base URL for the API.
            timeout: Request timeout in seconds.
            retry_config: Configuration for retry behavior.
            http_client: Optional pre-configured async httpx client.
        """
        self._validate_api_key(api_key)

        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retry_config = retry_config or RetryConfig()
        self.last_rate_limit: RateLimitInfo | None = None

        self._client = http_client or httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._default_headers(),
        )
        self._retry_handler = RetryHandler(self.retry_config)
        self._owns_client = http_client is None

    def _validate_api_key(self, api_key: str) -> None:
        """Validate API key format."""
        if not api_key:
            raise ValueError("API key is required")
        if not api_key.startswith(API_KEY_PREFIX):
            raise ValueError(f"API key must start with '{API_KEY_PREFIX}'. Got: {api_key[:10]}...")

    def _default_headers(self) -> dict[str, str]:
        """Get default headers for all requests."""
        return {
            API_KEY_HEADER: self.api_key,
            "Accept": "application/json",
            "User-Agent": "volare-signals-python/1.0.0",
        }

    def _parse_rate_limit(self, response: httpx.Response) -> RateLimitInfo:
        """Parse rate limit information from response headers."""
        headers = dict(response.headers)
        return RateLimitInfo.from_headers(headers)

    def _handle_error_response(
        self,
        response: httpx.Response,
        rate_limit: RateLimitInfo,
    ) -> None:
        """Handle error responses from the API."""
        try:
            error_data = response.json()
            error_response = ErrorResponse.model_validate(error_data)
        except Exception:
            error_response = ErrorResponse(
                error="UNKNOWN_ERROR",
                message=response.text or f"HTTP {response.status_code}",
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitExceededError(
                message=error_response.message,
                error_code=error_response.error,
                details=error_response.details,
                rate_limit=rate_limit,
                retry_after=int(retry_after) if retry_after else None,
            )

        raise VolareAPIError.from_response(
            error_response,
            response.status_code,
            rate_limit,
        )

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request to the API."""
        filtered_params = {k: v for k, v in (params or {}).items() if v is not None}

        async def make_request() -> httpx.Response:
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    params=filtered_params,
                )
            except httpx.ConnectError as e:
                raise NetworkError(f"Failed to connect to {self.base_url}", e)
            except httpx.TimeoutException as e:
                raise NetworkError(f"Request timed out after {self.timeout}s", e)
            except httpx.HTTPError as e:
                raise NetworkError(f"HTTP error occurred: {e}", e)

            rate_limit = self._parse_rate_limit(response)
            self.last_rate_limit = rate_limit

            if not response.is_success:
                self._handle_error_response(response, rate_limit)

            return response

        return await self._retry_handler.execute_async(make_request)

    async def _get(
        self,
        path: str,
        response_type: type[T],
        params: dict[str, Any] | None = None,
    ) -> APIResponse[T]:
        """Make an async GET request and parse the response."""
        response = await self._request("GET", path, params)
        rate_limit = self._parse_rate_limit(response)

        data = response_type.model_validate(response.json())
        return APIResponse(
            data=data,
            rate_limit=rate_limit,
            status_code=response.status_code,
        )

    async def ping(self) -> APIResponse[PingResponse]:
        """Check API connectivity and service status (async)."""
        return await self._get("/ping", PingResponse)

    async def get_rate_limit_status(self) -> RateLimitInfo:
        """Get current rate limit status (async)."""
        response = await self.ping()
        return response.rate_limit

    async def get_latest(
        self,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> APIResponse[LatestSignalsResponse]:
        """Get the most recent signals (async)."""
        if min_rating is not None and not 1 <= min_rating <= 10:
            raise ValueError("min_rating must be between 1 and 10")
        if max_rating is not None and not 1 <= max_rating <= 10:
            raise ValueError("max_rating must be between 1 and 10")

        return await self._get(
            "/signals/latest",
            LatestSignalsResponse,
            params={
                "min_rating": min_rating,
                "max_rating": max_rating,
            },
        )

    async def get_history(
        self,
        start_date: str | date_type,
        end_date: str | date_type,
        min_rating: int | None = None,
        max_rating: int | None = None,
    ) -> APIResponse[SignalHistoryResponse]:
        """Get historical signals for a date range (async)."""
        if min_rating is not None and not 1 <= min_rating <= 10:
            raise ValueError("min_rating must be between 1 and 10")
        if max_rating is not None and not 1 <= max_rating <= 10:
            raise ValueError("max_rating must be between 1 and 10")

        start_date_str = start_date.isoformat() if isinstance(start_date, date_type) else start_date
        end_date_str = end_date.isoformat() if isinstance(end_date, date_type) else end_date

        return await self._get(
            "/signals/history",
            SignalHistoryResponse,
            params={
                "start_date": start_date_str,
                "end_date": end_date_str,
                "min_rating": min_rating,
                "max_rating": max_rating,
            },
        )

    async def get_strong_buys(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[StrongBuysResponse]:
        """Get strong buy signals for a given date (async)."""
        date_str = date.isoformat() if isinstance(date, date_type) else date
        return await self._get(
            "/signals/strong-buys",
            StrongBuysResponse,
            params={"date": date_str, "limit": limit},
        )

    async def get_strong_sells(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[StrongSellsResponse]:
        """Get strong sell signals for a given date (async)."""
        date_str = date.isoformat() if isinstance(date, date_type) else date
        return await self._get(
            "/signals/strong-sells",
            StrongSellsResponse,
            params={"date": date_str, "limit": limit},
        )

    async def get_upgrades(
        self,
        date: str | date_type | None = None,
        min_change: int | None = None,
        limit: int | None = None,
    ) -> APIResponse[UpgradesResponse]:
        """Get upgraded signals for a given date (async)."""
        if min_change is not None and min_change < 1:
            raise ValueError("min_change must be a positive integer")

        date_str = date.isoformat() if isinstance(date, date_type) else date
        return await self._get(
            "/signals/upgrades",
            UpgradesResponse,
            params={"date": date_str, "min_change": min_change, "limit": limit},
        )

    async def get_downgrades(
        self,
        date: str | date_type | None = None,
        max_change: int | None = None,
        limit: int | None = None,
    ) -> APIResponse[DowngradesResponse]:
        """Get downgraded signals for a given date (async)."""
        if max_change is not None and max_change >= 0:
            raise ValueError("max_change must be a negative integer")

        date_str = date.isoformat() if isinstance(date, date_type) else date
        return await self._get(
            "/signals/downgrades",
            DowngradesResponse,
            params={"date": date_str, "max_change": max_change, "limit": limit},
        )

    async def get_new_signals(
        self,
        date: str | date_type | None = None,
        limit: int | None = None,
    ) -> APIResponse[NewSignalsResponse]:
        """Get new signals for a given date (async)."""
        date_str = date.isoformat() if isinstance(date, date_type) else date
        return await self._get(
            "/signals/new",
            NewSignalsResponse,
            params={"date": date_str, "limit": limit},
        )

    async def close(self) -> None:
        """Close the async HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> AsyncVolareSignalsClient:
        """Enter async context manager."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager and close client."""
        await self.close()

    def __repr__(self) -> str:
        return (
            f"AsyncVolareSignalsClient(base_url={self.base_url!r}, api_key={self.api_key[:8]}...)"
        )
