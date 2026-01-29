# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from typing_extensions import TypedDict

from .._types import SequenceNotStr

__all__ = ["EventListParams", "CustomRange"]


class EventListParams(TypedDict, total=False):
    custom_range: CustomRange
    """Filter events by time range"""

    customer_id: str
    """Filter events by customer ID"""

    feature_id: Union[str, SequenceNotStr[str]]
    """Filter by specific feature ID(s)"""

    limit: int
    """Number of items to return. Default 100, max 1000."""

    offset: int
    """Number of items to skip"""


class CustomRange(TypedDict, total=False):
    """Filter events by time range"""

    end: float
    """Filter events before this timestamp (epoch milliseconds)"""

    start: float
    """Filter events after this timestamp (epoch milliseconds)"""
