"""
Retry logic and rate limit handling for the Volare Signals API client.

This module provides utilities for handling retries with exponential backoff,
particularly for rate limit (429) responses.
"""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

from volare_signals.exceptions import RateLimitExceededError, RetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_retries: Maximum number of retry attempts. Set to 0 to disable retries.
        base_delay: Base delay in seconds before the first retry.
        max_delay: Maximum delay in seconds between retries.
        exponential_base: Base for exponential backoff calculation.
        jitter: Whether to add random jitter to delay times.
        retry_on_server_error: Whether to retry on 5xx server errors.
    """

    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retry_on_server_error: bool = True

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if self.base_delay <= 0:
            raise ValueError("base_delay must be positive")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base <= 1:
            raise ValueError("exponential_base must be > 1")


@dataclass
class RetryState:
    """
    Tracks the state of retry attempts.

    Attributes:
        attempt: Current attempt number (0-indexed).
        last_error: The last error that occurred.
        total_delay: Total time spent waiting between retries.
    """

    attempt: int = 0
    last_error: Exception | None = None
    total_delay: float = 0.0


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    retry_after: int | None = None,
) -> float:
    """
    Calculate the delay before the next retry attempt.

    Uses exponential backoff with optional jitter. If a Retry-After header
    value is provided, it takes precedence over the calculated delay.

    Args:
        attempt: Current attempt number (0-indexed).
        config: Retry configuration.
        retry_after: Value from Retry-After header, if present.

    Returns:
        Delay in seconds before the next retry.
    """
    if retry_after is not None and retry_after > 0:
        delay = float(retry_after)
    else:
        delay = config.base_delay * (config.exponential_base**attempt)

    delay = min(delay, config.max_delay)

    if config.jitter:
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)
        delay = max(0.1, delay)

    return delay


def should_retry(
    exception: Exception,
    config: RetryConfig,
    state: RetryState,
) -> bool:
    """
    Determine whether a request should be retried.

    Args:
        exception: The exception that occurred.
        config: Retry configuration.
        state: Current retry state.

    Returns:
        True if the request should be retried, False otherwise.
    """
    if state.attempt > config.max_retries:
        return False

    if isinstance(exception, RateLimitExceededError):
        return True

    if config.retry_on_server_error:
        from volare_signals.exceptions import ServerError

        if isinstance(exception, ServerError):
            return True

    from volare_signals.exceptions import NetworkError

    return isinstance(exception, NetworkError)


class RetryHandler:
    """
    Handler for executing requests with retry logic.

    This class encapsulates the retry logic and can be used to wrap
    any callable that might fail with retryable errors.

    Example:
        ```python
        handler = RetryHandler(config=RetryConfig(max_retries=3))
        result = handler.execute(lambda: make_api_request())
        ```
    """

    def __init__(self, config: RetryConfig | None = None) -> None:
        """
        Initialize the retry handler.

        Args:
            config: Retry configuration. Uses defaults if not provided.
        """
        self.config = config or RetryConfig()

    def execute(
        self,
        func: Callable[[], T],
        on_retry: Callable[[RetryState, float], None] | None = None,
    ) -> T:
        """
        Execute a function with retry logic.

        Args:
            func: The function to execute.
            on_retry: Optional callback called before each retry with
                     the current state and delay.

        Returns:
            The result of the function call.

        Raises:
            RetryExhaustedError: If all retry attempts are exhausted.
            VolareAPIError: If a non-retryable error occurs.
        """
        state = RetryState()

        while True:
            try:
                return func()
            except Exception as e:
                state.last_error = e
                state.attempt += 1

                if not should_retry(e, self.config, state):
                    if state.attempt > 1:
                        raise RetryExhaustedError(
                            attempts=state.attempt,
                            last_error=e,
                        ) from e
                    raise

                retry_after = None
                if isinstance(e, RateLimitExceededError):
                    retry_after = e.retry_after

                delay = calculate_delay(state.attempt - 1, self.config, retry_after)
                state.total_delay += delay

                logger.warning(
                    "Request failed (attempt %d/%d), retrying in %.2fs: %s",
                    state.attempt,
                    self.config.max_retries + 1,
                    delay,
                    e,
                )

                if on_retry:
                    on_retry(state, delay)

                time.sleep(delay)

    async def execute_async(
        self,
        func: Callable[[], Awaitable[T]],
        on_retry: Callable[[RetryState, float], None] | None = None,
    ) -> T:
        """
        Execute a function with retry logic (async version).

        Args:
            func: The async function to execute.
            on_retry: Optional callback called before each retry.

        Returns:
            The result of the function call.

        Raises:
            RetryExhaustedError: If all retry attempts are exhausted.
            VolareAPIError: If a non-retryable error occurs.
        """
        import asyncio

        state = RetryState()

        while True:
            try:
                return await func()
            except Exception as e:
                state.last_error = e
                state.attempt += 1

                if not should_retry(e, self.config, state):
                    if state.attempt > 1:
                        raise RetryExhaustedError(
                            attempts=state.attempt,
                            last_error=e,
                        ) from e
                    raise

                retry_after = None
                if isinstance(e, RateLimitExceededError):
                    retry_after = e.retry_after

                delay = calculate_delay(state.attempt - 1, self.config, retry_after)
                state.total_delay += delay

                logger.warning(
                    "Request failed (attempt %d/%d), retrying in %.2fs: %s",
                    state.attempt,
                    self.config.max_retries + 1,
                    delay,
                    e,
                )

                if on_retry:
                    on_retry(state, delay)

                await asyncio.sleep(delay)
