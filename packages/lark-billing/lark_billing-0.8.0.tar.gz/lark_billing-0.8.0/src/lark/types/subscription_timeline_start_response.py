# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from datetime import datetime
from typing_extensions import Literal, Annotated, TypeAlias

from .._utils import PropertyInfo
from .._models import BaseModel

__all__ = [
    "SubscriptionTimelineStartResponse",
    "Result",
    "ResultStartSubscriptionTimelineRequiresActionResponse",
    "ResultStartSubscriptionTimelineRequiresActionResponseAction",
    "ResultStartSubscriptionTimelineSuccessResponse",
    "ResultStartSubscriptionTimelineSuccessResponseSubscriptionTimeline",
]


class ResultStartSubscriptionTimelineRequiresActionResponseAction(BaseModel):
    """The action to take to complete the request."""

    checkout_url: str
    """The URL of the checkout page to redirect to in order to complete the request."""

    requires_action_type: Literal["checkout"]


class ResultStartSubscriptionTimelineRequiresActionResponse(BaseModel):
    action: ResultStartSubscriptionTimelineRequiresActionResponseAction
    """The action to take to complete the request."""

    result_type: Literal["requires_action"]


class ResultStartSubscriptionTimelineSuccessResponseSubscriptionTimeline(BaseModel):
    """The subscription timeline resource."""

    id: str

    created_at: datetime

    rate_card_id: str

    status: Literal["draft", "pending", "active", "completed"]

    subject_id: str

    subscription_id: Optional[str] = None

    updated_at: datetime


class ResultStartSubscriptionTimelineSuccessResponse(BaseModel):
    result_type: Literal["success"]

    subscription_timeline: ResultStartSubscriptionTimelineSuccessResponseSubscriptionTimeline
    """The subscription timeline resource."""


Result: TypeAlias = Annotated[
    Union[ResultStartSubscriptionTimelineRequiresActionResponse, ResultStartSubscriptionTimelineSuccessResponse],
    PropertyInfo(discriminator="result_type"),
]


class SubscriptionTimelineStartResponse(BaseModel):
    result: Result
    """The result of the request.

    If the request is successful, the subscription timeline resource will be
    returned. If the request is requires action, the action to take to complete the
    request will be returned.
    """
