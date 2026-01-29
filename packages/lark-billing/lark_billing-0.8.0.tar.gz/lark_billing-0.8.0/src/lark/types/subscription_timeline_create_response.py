# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["SubscriptionTimelineCreateResponse"]


class SubscriptionTimelineCreateResponse(BaseModel):
    id: str

    created_at: datetime

    rate_card_id: str

    status: Literal["draft", "pending", "active", "completed"]

    subject_id: str

    subscription_id: Optional[str] = None

    updated_at: datetime
