# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import typing
from typing_extensions import Literal

from .._models import BaseModel

__all__ = [
    "CustomerListResponse",
    "List",
    "ListBalances",
    "ListBalancesReset",
    "ListBalancesBreakdown",
    "ListBalancesBreakdownReset",
    "ListBalancesFeature",
    "ListBalancesFeatureCreditSchema",
    "ListBalancesFeatureDisplay",
    "ListBalancesRollover",
    "ListScheduledSubscription",
    "ListScheduledSubscriptionPlan",
    "ListScheduledSubscriptionPlanFeature",
    "ListScheduledSubscriptionPlanFeaturePrice",
    "ListScheduledSubscriptionPlanFeaturePriceTier",
    "ListScheduledSubscriptionPlanFeatureReset",
    "ListScheduledSubscriptionPlanFeatureDisplay",
    "ListScheduledSubscriptionPlanFeatureFeature",
    "ListScheduledSubscriptionPlanFeatureFeatureCreditSchema",
    "ListScheduledSubscriptionPlanFeatureFeatureDisplay",
    "ListScheduledSubscriptionPlanFeatureProration",
    "ListScheduledSubscriptionPlanFeatureRollover",
    "ListScheduledSubscriptionPlanPrice",
    "ListScheduledSubscriptionPlanPriceDisplay",
    "ListScheduledSubscriptionPlanCustomerEligibility",
    "ListScheduledSubscriptionPlanFreeTrial",
    "ListSubscription",
    "ListSubscriptionPlan",
    "ListSubscriptionPlanFeature",
    "ListSubscriptionPlanFeaturePrice",
    "ListSubscriptionPlanFeaturePriceTier",
    "ListSubscriptionPlanFeatureReset",
    "ListSubscriptionPlanFeatureDisplay",
    "ListSubscriptionPlanFeatureFeature",
    "ListSubscriptionPlanFeatureFeatureCreditSchema",
    "ListSubscriptionPlanFeatureFeatureDisplay",
    "ListSubscriptionPlanFeatureProration",
    "ListSubscriptionPlanFeatureRollover",
    "ListSubscriptionPlanPrice",
    "ListSubscriptionPlanPriceDisplay",
    "ListSubscriptionPlanCustomerEligibility",
    "ListSubscriptionPlanFreeTrial",
]


class ListBalancesReset(BaseModel):
    interval: Literal["one_off", "minute", "hour", "day", "week", "month", "quarter", "semi_annual", "year", "multiple"]

    resets_at: typing.Optional[float] = None

    interval_count: typing.Optional[float] = None


class ListBalancesBreakdownReset(BaseModel):
    interval: Literal["one_off", "minute", "hour", "day", "week", "month", "quarter", "semi_annual", "year", "multiple"]

    resets_at: typing.Optional[float] = None

    interval_count: typing.Optional[float] = None


class ListBalancesBreakdown(BaseModel):
    id: str

    current_balance: float

    expires_at: typing.Optional[float] = None

    granted_balance: float

    max_purchase: typing.Optional[float] = None

    overage_allowed: bool

    plan_id: typing.Optional[str] = None

    prepaid_quantity: float

    purchased_balance: float

    reset: typing.Optional[ListBalancesBreakdownReset] = None

    usage: float


class ListBalancesFeatureCreditSchema(BaseModel):
    credit_cost: float

    metered_feature_id: str


class ListBalancesFeatureDisplay(BaseModel):
    plural: typing.Optional[str] = None

    singular: typing.Optional[str] = None


class ListBalancesFeature(BaseModel):
    id: str

    archived: bool

    consumable: bool

    name: str

    type: Literal["boolean", "metered", "credit_system"]

    credit_schema: typing.Optional[typing.List[ListBalancesFeatureCreditSchema]] = None

    display: typing.Optional[ListBalancesFeatureDisplay] = None

    event_names: typing.Optional[typing.List[str]] = None


class ListBalancesRollover(BaseModel):
    balance: float

    expires_at: float


class ListBalances(BaseModel):
    current_balance: float

    feature_id: str

    granted_balance: float

    max_purchase: typing.Optional[float] = None

    overage_allowed: bool

    plan_id: typing.Optional[str] = None

    purchased_balance: float

    reset: typing.Optional[ListBalancesReset] = None

    unlimited: bool

    usage: float

    breakdown: typing.Optional[typing.List[ListBalancesBreakdown]] = None

    feature: typing.Optional[ListBalancesFeature] = None

    rollovers: typing.Optional[typing.List[ListBalancesRollover]] = None


class ListScheduledSubscriptionPlanFeaturePriceTier(BaseModel):
    amount: float

    to: typing.Union[float, Literal["inf"]]


class ListScheduledSubscriptionPlanFeaturePrice(BaseModel):
    billing_units: float

    interval: Literal["one_off", "week", "month", "quarter", "semi_annual", "year"]

    max_purchase: typing.Optional[float] = None

    usage_model: Literal["prepaid", "pay_per_use"]

    amount: typing.Optional[float] = None

    interval_count: typing.Optional[float] = None

    tiers: typing.Optional[typing.List[ListScheduledSubscriptionPlanFeaturePriceTier]] = None


class ListScheduledSubscriptionPlanFeatureReset(BaseModel):
    interval: Literal["one_off", "minute", "hour", "day", "week", "month", "quarter", "semi_annual", "year"]

    reset_when_enabled: bool

    interval_count: typing.Optional[float] = None


class ListScheduledSubscriptionPlanFeatureDisplay(BaseModel):
    primary_text: str

    secondary_text: typing.Optional[str] = None


class ListScheduledSubscriptionPlanFeatureFeatureCreditSchema(BaseModel):
    credit_cost: float
    """The credit cost of the metered feature."""

    metered_feature_id: str
    """The ID of the metered feature (should be a single_use feature)."""


class ListScheduledSubscriptionPlanFeatureFeatureDisplay(BaseModel):
    """Singular and plural display names for the feature."""

    plural: str
    """The plural display name for the feature."""

    singular: str
    """The singular display name for the feature."""


class ListScheduledSubscriptionPlanFeatureFeature(BaseModel):
    id: str
    """
    The ID of the feature, used to refer to it in other API calls like /track or
    /check.
    """

    type: Literal["static", "boolean", "single_use", "continuous_use", "credit_system"]
    """The type of the feature"""

    archived: typing.Optional[bool] = None
    """Whether or not the feature is archived."""

    credit_schema: typing.Optional[typing.List[ListScheduledSubscriptionPlanFeatureFeatureCreditSchema]] = None
    """Credit cost schema for credit system features."""

    display: typing.Optional[ListScheduledSubscriptionPlanFeatureFeatureDisplay] = None
    """Singular and plural display names for the feature."""

    name: typing.Optional[str] = None
    """The name of the feature."""


class ListScheduledSubscriptionPlanFeatureProration(BaseModel):
    on_decrease: typing.Optional[
        Literal["prorate", "prorate_immediately", "prorate_next_cycle", "none", "no_prorations"]
    ] = None

    on_increase: typing.Optional[
        Literal["bill_immediately", "prorate_immediately", "prorate_next_cycle", "bill_next_cycle"]
    ] = None


class ListScheduledSubscriptionPlanFeatureRollover(BaseModel):
    expiry_duration_type: Literal["month", "forever"]

    max: typing.Optional[float] = None

    expiry_duration_length: typing.Optional[float] = None


class ListScheduledSubscriptionPlanFeature(BaseModel):
    feature_id: str

    granted_balance: float

    price: typing.Optional[ListScheduledSubscriptionPlanFeaturePrice] = None

    reset: typing.Optional[ListScheduledSubscriptionPlanFeatureReset] = None

    unlimited: bool

    display: typing.Optional[ListScheduledSubscriptionPlanFeatureDisplay] = None

    feature: typing.Optional[ListScheduledSubscriptionPlanFeatureFeature] = None

    proration: typing.Optional[ListScheduledSubscriptionPlanFeatureProration] = None

    rollover: typing.Optional[ListScheduledSubscriptionPlanFeatureRollover] = None


class ListScheduledSubscriptionPlanPriceDisplay(BaseModel):
    primary_text: str

    secondary_text: typing.Optional[str] = None


class ListScheduledSubscriptionPlanPrice(BaseModel):
    amount: float

    interval: Literal["one_off", "week", "month", "quarter", "semi_annual", "year"]

    display: typing.Optional[ListScheduledSubscriptionPlanPriceDisplay] = None

    interval_count: typing.Optional[float] = None


class ListScheduledSubscriptionPlanCustomerEligibility(BaseModel):
    scenario: Literal["scheduled", "active", "new", "renew", "upgrade", "downgrade", "cancel", "expired", "past_due"]

    trial_available: typing.Optional[bool] = None


class ListScheduledSubscriptionPlanFreeTrial(BaseModel):
    card_required: bool

    duration_length: float

    duration_type: Literal["day", "month", "year"]


class ListScheduledSubscriptionPlan(BaseModel):
    id: str

    add_on: bool

    archived: bool

    base_variant_id: typing.Optional[str] = None

    created_at: float

    default: bool

    description: typing.Optional[str] = None

    env: Literal["sandbox", "live"]

    features: typing.List[ListScheduledSubscriptionPlanFeature]

    group: typing.Optional[str] = None

    name: str

    price: typing.Optional[ListScheduledSubscriptionPlanPrice] = None

    version: float

    customer_eligibility: typing.Optional[ListScheduledSubscriptionPlanCustomerEligibility] = None

    free_trial: typing.Optional[ListScheduledSubscriptionPlanFreeTrial] = None


class ListScheduledSubscription(BaseModel):
    add_on: bool

    canceled_at: typing.Optional[float] = None

    current_period_end: typing.Optional[float] = None

    current_period_start: typing.Optional[float] = None

    default: bool

    expires_at: typing.Optional[float] = None

    past_due: bool

    plan_id: str

    quantity: float

    started_at: float

    status: Literal["active", "scheduled", "expired"]

    trial_ends_at: typing.Optional[float] = None

    plan: typing.Optional[ListScheduledSubscriptionPlan] = None


class ListSubscriptionPlanFeaturePriceTier(BaseModel):
    amount: float

    to: typing.Union[float, Literal["inf"]]


class ListSubscriptionPlanFeaturePrice(BaseModel):
    billing_units: float

    interval: Literal["one_off", "week", "month", "quarter", "semi_annual", "year"]

    max_purchase: typing.Optional[float] = None

    usage_model: Literal["prepaid", "pay_per_use"]

    amount: typing.Optional[float] = None

    interval_count: typing.Optional[float] = None

    tiers: typing.Optional[typing.List[ListSubscriptionPlanFeaturePriceTier]] = None


class ListSubscriptionPlanFeatureReset(BaseModel):
    interval: Literal["one_off", "minute", "hour", "day", "week", "month", "quarter", "semi_annual", "year"]

    reset_when_enabled: bool

    interval_count: typing.Optional[float] = None


class ListSubscriptionPlanFeatureDisplay(BaseModel):
    primary_text: str

    secondary_text: typing.Optional[str] = None


class ListSubscriptionPlanFeatureFeatureCreditSchema(BaseModel):
    credit_cost: float
    """The credit cost of the metered feature."""

    metered_feature_id: str
    """The ID of the metered feature (should be a single_use feature)."""


class ListSubscriptionPlanFeatureFeatureDisplay(BaseModel):
    """Singular and plural display names for the feature."""

    plural: str
    """The plural display name for the feature."""

    singular: str
    """The singular display name for the feature."""


class ListSubscriptionPlanFeatureFeature(BaseModel):
    id: str
    """
    The ID of the feature, used to refer to it in other API calls like /track or
    /check.
    """

    type: Literal["static", "boolean", "single_use", "continuous_use", "credit_system"]
    """The type of the feature"""

    archived: typing.Optional[bool] = None
    """Whether or not the feature is archived."""

    credit_schema: typing.Optional[typing.List[ListSubscriptionPlanFeatureFeatureCreditSchema]] = None
    """Credit cost schema for credit system features."""

    display: typing.Optional[ListSubscriptionPlanFeatureFeatureDisplay] = None
    """Singular and plural display names for the feature."""

    name: typing.Optional[str] = None
    """The name of the feature."""


class ListSubscriptionPlanFeatureProration(BaseModel):
    on_decrease: typing.Optional[
        Literal["prorate", "prorate_immediately", "prorate_next_cycle", "none", "no_prorations"]
    ] = None

    on_increase: typing.Optional[
        Literal["bill_immediately", "prorate_immediately", "prorate_next_cycle", "bill_next_cycle"]
    ] = None


class ListSubscriptionPlanFeatureRollover(BaseModel):
    expiry_duration_type: Literal["month", "forever"]

    max: typing.Optional[float] = None

    expiry_duration_length: typing.Optional[float] = None


class ListSubscriptionPlanFeature(BaseModel):
    feature_id: str

    granted_balance: float

    price: typing.Optional[ListSubscriptionPlanFeaturePrice] = None

    reset: typing.Optional[ListSubscriptionPlanFeatureReset] = None

    unlimited: bool

    display: typing.Optional[ListSubscriptionPlanFeatureDisplay] = None

    feature: typing.Optional[ListSubscriptionPlanFeatureFeature] = None

    proration: typing.Optional[ListSubscriptionPlanFeatureProration] = None

    rollover: typing.Optional[ListSubscriptionPlanFeatureRollover] = None


class ListSubscriptionPlanPriceDisplay(BaseModel):
    primary_text: str

    secondary_text: typing.Optional[str] = None


class ListSubscriptionPlanPrice(BaseModel):
    amount: float

    interval: Literal["one_off", "week", "month", "quarter", "semi_annual", "year"]

    display: typing.Optional[ListSubscriptionPlanPriceDisplay] = None

    interval_count: typing.Optional[float] = None


class ListSubscriptionPlanCustomerEligibility(BaseModel):
    scenario: Literal["scheduled", "active", "new", "renew", "upgrade", "downgrade", "cancel", "expired", "past_due"]

    trial_available: typing.Optional[bool] = None


class ListSubscriptionPlanFreeTrial(BaseModel):
    card_required: bool

    duration_length: float

    duration_type: Literal["day", "month", "year"]


class ListSubscriptionPlan(BaseModel):
    id: str

    add_on: bool

    archived: bool

    base_variant_id: typing.Optional[str] = None

    created_at: float

    default: bool

    description: typing.Optional[str] = None

    env: Literal["sandbox", "live"]

    features: typing.List[ListSubscriptionPlanFeature]

    group: typing.Optional[str] = None

    name: str

    price: typing.Optional[ListSubscriptionPlanPrice] = None

    version: float

    customer_eligibility: typing.Optional[ListSubscriptionPlanCustomerEligibility] = None

    free_trial: typing.Optional[ListSubscriptionPlanFreeTrial] = None


class ListSubscription(BaseModel):
    add_on: bool

    canceled_at: typing.Optional[float] = None

    current_period_end: typing.Optional[float] = None

    current_period_start: typing.Optional[float] = None

    default: bool

    expires_at: typing.Optional[float] = None

    past_due: bool

    plan_id: str

    quantity: float

    started_at: float

    status: Literal["active", "scheduled", "expired"]

    trial_ends_at: typing.Optional[float] = None

    plan: typing.Optional[ListSubscriptionPlan] = None


class List(BaseModel):
    id: typing.Optional[str] = None

    balances: typing.Dict[str, ListBalances]

    created_at: float

    email: typing.Optional[str] = None

    env: Literal["sandbox", "live"]

    fingerprint: typing.Optional[str] = None

    metadata: typing.Dict[str, object]

    name: typing.Optional[str] = None

    scheduled_subscriptions: typing.List[ListScheduledSubscription]

    stripe_id: typing.Optional[str] = None

    subscriptions: typing.List[ListSubscription]

    autumn_id: typing.Optional[str] = None


class CustomerListResponse(BaseModel):
    has_more: bool
    """Whether more results exist after this page"""

    limit: float
    """Limit passed in the request"""

    list: typing.List[List]
    """Array of items for current page"""

    offset: float
    """Current offset position"""

    total: float
    """Total number of items returned in the current page"""
