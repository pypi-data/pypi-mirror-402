# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SubscriptionTimelineCreateParams"]


class SubscriptionTimelineCreateParams(TypedDict, total=False):
    rate_card_id: Required[str]
    """The ID of the rate card to create the subscription timeline for."""

    subject_id: Required[str]
    """The ID of the subject to create the subscription timeline for."""
