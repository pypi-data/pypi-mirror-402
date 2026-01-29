# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo
from .checkout_callback_param import CheckoutCallbackParam

__all__ = ["SubscriptionTimelineStartParams"]


class SubscriptionTimelineStartParams(TypedDict, total=False):
    checkout_callback_urls: Required[CheckoutCallbackParam]
    """
    The URLs to redirect to after the checkout is completed or cancelled, if a
    checkout is required.
    """

    create_checkout_session: Required[Literal["when_required", "always"]]
    """
    Determines whether a checkout session is always required even if the subject has
    a payment method on file. By default, if the subject has a payment method on
    file, the subscription will be created and billed for immediately.
    """

    effective_at: Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]
    """When the subscription should become active.

    If not provided, the current date and time will be used.
    """
