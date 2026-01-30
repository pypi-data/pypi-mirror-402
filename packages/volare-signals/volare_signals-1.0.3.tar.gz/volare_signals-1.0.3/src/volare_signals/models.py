"""
Data models for the Volare Signals API.

This module contains Pydantic models and dataclasses representing all
request/response structures used by the Volare Signals API.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Annotated, Any, Generic, Literal, TypeVar

from pydantic import BaseModel, BeforeValidator, Field, field_validator


def coerce_int(v: Any) -> int:
    """Coerce string or int to int."""
    if v is None:
        raise ValueError("Value cannot be None")
    return int(v)


def coerce_optional_int(v: Any) -> int | None:
    """Coerce string or int to optional int."""
    if v is None or v == "":
        return None
    return int(v)


def coerce_float(v: Any) -> float:
    """Coerce string or float to float."""
    if v is None:
        raise ValueError("Value cannot be None")
    return float(v)


def coerce_optional_float(v: Any) -> float | None:
    """Coerce string or float to optional float."""
    if v is None or v == "":
        return None
    return float(v)


# Annotated types for coercion
CoercedInt = Annotated[int, BeforeValidator(coerce_int)]
CoercedOptionalInt = Annotated[int | None, BeforeValidator(coerce_optional_int)]
CoercedFloat = Annotated[float, BeforeValidator(coerce_float)]
CoercedOptionalFloat = Annotated[float | None, BeforeValidator(coerce_optional_float)]


class Side(str, Enum):
    """Trading side for a signal."""

    LONG = "long"
    SHORT = "short"


class SupportingAlgo(BaseModel):
    """
    Represents an algorithm that contributed to a signal's rating.

    Attributes:
        algo_id: Unique identifier for the algorithm.
        weight: The weight/contribution of this algorithm to the overall rating.
        direction: The direction of the algorithm signal (long/short).
    """

    algo_id: str = Field(..., alias="algoId", description="Unique identifier for the algorithm")
    weight: CoercedFloat = Field(..., ge=0.0, description="Weight of the algorithm's contribution")
    direction: str | None = Field(None, description="Direction of the algorithm signal")

    model_config = {"populate_by_name": True}


class RatingBreakdown(BaseModel):
    """
    Breakdown of how a signal's rating was calculated.

    Attributes:
        total_weight: Total combined weight from all contributing algorithms.
        algo_count: Number of algorithms that contributed to this signal.
    """

    total_weight: CoercedFloat = Field(
        ..., alias="totalWeight", description="Total combined weight"
    )
    algo_count: CoercedInt = Field(
        ..., alias="algoCount", description="Number of contributing algorithms"
    )

    model_config = {"populate_by_name": True}


class Signal(BaseModel):
    """
    Represents a trading signal from the Volare platform.

    Attributes:
        date: The date of the signal in YYYY-MM-DD format.
        symbol: The ticker symbol for the instrument.
        rating: Signal strength rating from 1 (weakest) to 10 (strongest).
        side: Whether the signal is for a long or short position.
        previous_rating: The previous rating if this is an update, None for new signals.
        rating_change: The change in rating from the previous value.
        entry_price: Suggested entry price, if available.
        supporting_algos: List of algorithms that contributed to this signal.
        rating_breakdown: Detailed breakdown of rating components, if available.
    """

    date: str = Field(..., description="Signal date in YYYY-MM-DD format")
    symbol: str = Field(..., min_length=1, max_length=10, description="Ticker symbol")
    rating: CoercedInt = Field(..., ge=1, le=10, description="Signal rating from 1-10")
    side: Side = Field(..., description="Trading side (long or short)")
    previous_rating: CoercedOptionalInt = Field(
        None,
        alias="previousRating",
        ge=1,
        le=10,
        description="Previous rating if this is an update",
    )
    rating_change: CoercedInt = Field(
        ..., alias="ratingChange", description="Change in rating from previous value"
    )
    entry_price: CoercedOptionalFloat = Field(
        None, alias="entryPrice", gt=0, description="Suggested entry price"
    )
    supporting_algos: list[SupportingAlgo] = Field(
        default_factory=list,
        alias="supportingAlgos",
        description="Algorithms contributing to this signal",
    )
    rating_breakdown: RatingBreakdown | None = Field(
        None, alias="ratingBreakdown", description="Detailed rating breakdown"
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "date": "2024-01-15",
                "symbol": "AAPL",
                "rating": 8,
                "side": "long",
                "previousRating": 6,
                "ratingChange": 2,
                "entryPrice": 185.50,
                "supportingAlgos": [
                    {"algoId": "momentum_v2", "weight": 0.35},
                    {"algoId": "trend_follower", "weight": 0.25},
                ],
                "ratingBreakdown": None,
            }
        },
    }

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Validate that date is in YYYY-MM-DD format."""
        try:
            date.fromisoformat(v)
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v


class PingResponse(BaseModel):
    """Response from the /ping endpoint."""

    status: str = Field(..., description="Service status")
    timestamp: str | None = Field(None, description="Server timestamp")
    version: str | None = Field(None, description="API version")
    service: str | None = Field(None, description="Service name")


class SignalHistoryResponse(BaseModel):
    """Response from the /signals/history endpoint."""

    start_date: str = Field(..., alias="startDate", description="Start date of the query range")
    end_date: str = Field(..., alias="endDate", description="End date of the query range")
    signals: list[Signal] = Field(default_factory=list, description="List of signals")
    count: int = Field(..., ge=0, description="Number of signals returned")

    model_config = {"populate_by_name": True}


class LatestSignalsResponse(BaseModel):
    """Response from the /signals/latest endpoint."""

    date: str = Field(..., description="Date of the most recent signals")
    signals: list[Signal] = Field(default_factory=list, description="List of signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    message: str | None = Field(None, description="Optional message (e.g., 'No signals found')")


class RatingRange(BaseModel):
    """Rating range as returned by the API."""

    min: int = Field(..., ge=1, le=10)
    max: int = Field(..., ge=1, le=10)


class StrongBuysResponse(BaseModel):
    """Response from the /signals/strong-buys endpoint."""

    date: str = Field(..., description="Query date")
    signals: list[Signal] = Field(default_factory=list, description="List of strong buy signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    filter: Literal["strong-buys"] = Field(..., description="Applied filter type")
    rating_range: RatingRange = Field(
        ..., alias="ratingRange", description="Rating range for strong buys"
    )

    model_config = {"populate_by_name": True}


class StrongSellsResponse(BaseModel):
    """Response from the /signals/strong-sells endpoint."""

    date: str = Field(..., description="Query date")
    signals: list[Signal] = Field(default_factory=list, description="List of strong sell signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    filter: Literal["strong-sells"] = Field(..., description="Applied filter type")
    rating_range: RatingRange = Field(
        ..., alias="ratingRange", description="Rating range for strong sells"
    )

    model_config = {"populate_by_name": True}


class UpgradesResponse(BaseModel):
    """Response from the /signals/upgrades endpoint."""

    date: str = Field(..., description="Query date")
    signals: list[Signal] = Field(default_factory=list, description="List of upgraded signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    filter: Literal["upgrades"] = Field(..., description="Applied filter type")
    min_change: int = Field(
        ..., alias="minChange", ge=1, description="Minimum rating change for upgrades"
    )

    model_config = {"populate_by_name": True}


class DowngradesResponse(BaseModel):
    """Response from the /signals/downgrades endpoint."""

    date: str = Field(..., description="Query date")
    signals: list[Signal] = Field(default_factory=list, description="List of downgraded signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    filter: Literal["downgrades"] = Field(..., description="Applied filter type")
    max_change: int = Field(
        ...,
        alias="maxChange",
        le=-1,
        description="Maximum (most negative) rating change for downgrades",
    )

    model_config = {"populate_by_name": True}


class NewSignalsResponse(BaseModel):
    """Response from the /signals/new endpoint."""

    date: str = Field(..., description="Query date")
    signals: list[Signal] = Field(default_factory=list, description="List of new signals")
    count: int = Field(..., ge=0, description="Number of signals returned")
    filter: Literal["new"] = Field(..., description="Applied filter type")
    description: str | None = Field(None, description="Description of the filter")

    model_config = {"populate_by_name": True}


class ErrorResponse(BaseModel):
    """
    Standard error response from the Volare API.

    Attributes:
        error: Machine-readable error code.
        message: Human-readable error message.
        details: Additional error details, if available.
        field: The field that caused the error, for validation errors.
    """

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: str | None = Field(None, description="Additional error details")
    field: str | None = Field(None, description="Field causing validation error")


@dataclass
class RateLimitInfo:
    """
    Rate limit information extracted from API response headers.

    Attributes:
        limit_per_minute: Maximum requests allowed per minute.
        limit_per_day: Maximum requests allowed per day.
        remaining_minute: Requests remaining in current minute window.
        remaining_day: Requests remaining in current day window.
        reset_minute: Unix timestamp when minute limit resets.
        reset_day: Unix timestamp when day limit resets.
    """

    limit_per_minute: int = 60
    limit_per_day: int = 500
    remaining_minute: int | None = None
    remaining_day: int | None = None
    reset_minute: int | None = None
    reset_day: int | None = None

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> RateLimitInfo:
        """
        Parse rate limit information from response headers.

        Args:
            headers: Response headers dictionary.

        Returns:
            RateLimitInfo instance with parsed values.
        """
        # Normalize headers to lowercase for case-insensitive lookup
        lower_headers = {k.lower(): v for k, v in headers.items()}

        def get_header(name: str) -> str | None:
            return lower_headers.get(name.lower())

        def safe_int(value: str | None) -> int | None:
            if value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None

        return cls(
            limit_per_minute=safe_int(get_header("X-RateLimit-Limit-Minute")) or 60,
            limit_per_day=safe_int(get_header("X-RateLimit-Limit-Daily"))
            or safe_int(get_header("X-RateLimit-Limit-Day"))
            or 500,
            remaining_minute=safe_int(get_header("X-RateLimit-Remaining-Minute")),
            remaining_day=safe_int(get_header("X-RateLimit-Remaining-Daily"))
            or safe_int(get_header("X-RateLimit-Remaining-Day")),
            reset_minute=safe_int(get_header("X-RateLimit-Reset-Minute")),
            reset_day=safe_int(get_header("X-RateLimit-Reset-Daily"))
            or safe_int(get_header("X-RateLimit-Reset-Day")),
        )

    @property
    def is_minute_exhausted(self) -> bool:
        """Check if minute rate limit is exhausted."""
        return self.remaining_minute is not None and self.remaining_minute <= 0

    @property
    def is_day_exhausted(self) -> bool:
        """Check if daily rate limit is exhausted."""
        return self.remaining_day is not None and self.remaining_day <= 0


T = TypeVar("T")


@dataclass
class APIResponse(Generic[T]):
    """
    Generic wrapper for API responses containing both data and metadata.

    Type Parameters:
        T: The type of the response data.

    Attributes:
        data: The parsed response data.
        rate_limit: Rate limit information from response headers.
        status_code: HTTP status code of the response.
    """

    data: T
    rate_limit: RateLimitInfo
    status_code: int = 200
