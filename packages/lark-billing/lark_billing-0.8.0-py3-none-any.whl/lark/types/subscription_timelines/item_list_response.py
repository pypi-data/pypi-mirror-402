# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime

from ..._models import BaseModel

__all__ = ["ItemListResponse", "Item", "ItemPeriod", "ItemSubscriptionInput"]


class ItemPeriod(BaseModel):
    end: Optional[datetime] = None

    start: datetime

    inclusive_end: Optional[bool] = None

    inclusive_start: Optional[bool] = None


class ItemSubscriptionInput(BaseModel):
    fixed_rate_quantities: Dict[str, str]

    rate_card_id: str

    rate_price_multipliers: Dict[str, str]


class Item(BaseModel):
    id: str

    created_at: datetime

    period: ItemPeriod

    subscription_input: ItemSubscriptionInput

    subscription_timeline_id: str

    updated_at: datetime


class ItemListResponse(BaseModel):
    has_more: bool

    items: List[Item]
