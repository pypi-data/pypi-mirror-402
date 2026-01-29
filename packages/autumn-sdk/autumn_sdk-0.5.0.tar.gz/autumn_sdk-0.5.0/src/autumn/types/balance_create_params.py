# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, TypedDict

__all__ = ["BalanceCreateParams", "Reset"]


class BalanceCreateParams(TypedDict, total=False):
    customer_id: Required[str]
    """The customer ID to assign the balance to"""

    feature_id: Required[str]
    """The feature ID to create the balance for"""

    entity_id: str
    """Entity ID for entity-scoped balances"""

    expires_at: float
    """Unix timestamp (milliseconds) when the balance expires"""

    granted_balance: float
    """The initial balance amount to grant"""

    reset: Reset
    """Reset configuration for the balance"""

    unlimited: bool
    """Whether the balance is unlimited"""


class Reset(TypedDict, total=False):
    """Reset configuration for the balance"""

    interval: Required[Literal["one_off", "minute", "hour", "day", "week", "month", "quarter", "semi_annual", "year"]]

    interval_count: float
