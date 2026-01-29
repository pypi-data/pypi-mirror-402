# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable
from datetime import datetime
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ItemCreateParams", "Item", "ItemPeriod", "ItemSubscriptionInput"]


class ItemCreateParams(TypedDict, total=False):
    items: Required[Iterable[Item]]
    """The items to create for the subscription timeline."""


class ItemPeriod(TypedDict, total=False):
    """The period of the subscription timeline item."""

    end: Required[Annotated[Union[str, datetime, None], PropertyInfo(format="iso8601")]]

    start: Required[Annotated[Union[str, datetime], PropertyInfo(format="iso8601")]]

    inclusive_end: bool

    inclusive_start: bool


class ItemSubscriptionInput(TypedDict, total=False):
    """The subscription input for the subscription timeline item."""

    fixed_rate_quantities: Required[Dict[str, Union[float, str]]]
    """The quantities of the fixed rates to use for the subscription timeline item."""

    rate_card_id: Required[str]
    """The ID of the rate card to use for the subscription timeline item."""

    rate_price_multipliers: Required[Dict[str, Union[float, str]]]
    """The price multipliers to use for the subscription timeline item."""


class Item(TypedDict, total=False):
    period: Required[ItemPeriod]
    """The period of the subscription timeline item."""

    subscription_input: Required[ItemSubscriptionInput]
    """The subscription input for the subscription timeline item."""
