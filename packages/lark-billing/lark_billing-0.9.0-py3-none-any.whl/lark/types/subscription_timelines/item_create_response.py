# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from ..._models import BaseModel

__all__ = [
    "ItemCreateResponse",
    "ItemCreateResponseItem",
    "ItemCreateResponseItemPeriod",
    "ItemCreateResponseItemSubscriptionInput",
]


class ItemCreateResponseItemPeriod(BaseModel):
    end: Optional[datetime] = None

    start: datetime

    inclusive_end: Optional[bool] = None

    inclusive_start: Optional[bool] = None


class ItemCreateResponseItemSubscriptionInput(BaseModel):
    fixed_rate_quantities: Dict[str, str]

    rate_card_id: str

    rate_price_multipliers: Dict[str, str]


class ItemCreateResponseItem(BaseModel):
    id: str

    created_at: datetime

    period: ItemCreateResponseItemPeriod

    subscription_input: ItemCreateResponseItemSubscriptionInput

    subscription_timeline_id: str

    updated_at: datetime


ItemCreateResponse: TypeAlias = List[ItemCreateResponseItem]
