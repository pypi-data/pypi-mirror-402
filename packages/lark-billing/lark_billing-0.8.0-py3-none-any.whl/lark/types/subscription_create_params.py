# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Optional
from typing_extensions import Literal, Required, TypedDict

from .checkout_callback_param import CheckoutCallbackParam

__all__ = ["SubscriptionCreateParams"]


class SubscriptionCreateParams(TypedDict, total=False):
    rate_card_id: Required[str]
    """The ID of the rate card to use for the subscription."""

    subject_id: Required[str]
    """The ID or external ID of the subject to create the subscription for."""

    checkout_callback_urls: Optional[CheckoutCallbackParam]
    """
    The URLs to redirect to after the checkout is completed or cancelled, if a
    checkout is required.
    """

    create_checkout_session: Literal["when_required", "always"]
    """
    Determines whether a checkout session is always required even if the subject has
    a payment method on file. By default, if the subject has a payment method on
    file or the subscription is for a free plan, the subscription will be created
    and billed for immediately (if for a paid plan).
    """

    fixed_rate_quantities: Dict[str, Union[float, str]]
    """The quantities of the fixed rates to use for the subscription.

    Each quantity should be specified as a key-value pair, where the key is the
    `code` of the fixed rate and the value is the quantity. All fixed rates must
    have a quantity specified.
    """

    metadata: Dict[str, str]
    """Additional metadata about the subscription.

    You may use this to store any custom data about the subscription.
    """

    rate_price_multipliers: Dict[str, Union[float, str]]
    """Pricing multipliers to apply to the rate amounts.

    Each price multiplier should be specified as a key-value pair, where the key is
    the `code` of the rate and the value is the price multiplier. Typically, pricing
    multipliers are used to apply a discount to a rate. For example, if a rate is
    $10 per seat and the price multiplier for the `seats` rate is 0.5, the
    discounted rate amount will be $5 per seat.
    """

    subscription_timeline_id: Optional[str]
    """The ID of the subscription timeline to use for the subscription."""
