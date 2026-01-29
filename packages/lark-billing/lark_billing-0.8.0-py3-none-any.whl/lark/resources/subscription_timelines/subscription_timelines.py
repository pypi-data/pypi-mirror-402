# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import datetime
from typing_extensions import Literal

import httpx

from .items import (
    ItemsResource,
    AsyncItemsResource,
    ItemsResourceWithRawResponse,
    AsyncItemsResourceWithRawResponse,
    ItemsResourceWithStreamingResponse,
    AsyncItemsResourceWithStreamingResponse,
)
from ...types import (
    subscription_timeline_list_params,
    subscription_timeline_start_params,
    subscription_timeline_create_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.checkout_callback_param import CheckoutCallbackParam
from ...types.subscription_timeline_list_response import SubscriptionTimelineListResponse
from ...types.subscription_timeline_start_response import SubscriptionTimelineStartResponse
from ...types.subscription_timeline_create_response import SubscriptionTimelineCreateResponse
from ...types.subscription_timeline_retrieve_response import SubscriptionTimelineRetrieveResponse

__all__ = ["SubscriptionTimelinesResource", "AsyncSubscriptionTimelinesResource"]


class SubscriptionTimelinesResource(SyncAPIResource):
    @cached_property
    def items(self) -> ItemsResource:
        return ItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> SubscriptionTimelinesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/uselark/lark-billing-python#accessing-raw-response-data-eg-headers
        """
        return SubscriptionTimelinesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SubscriptionTimelinesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/uselark/lark-billing-python#with_streaming_response
        """
        return SubscriptionTimelinesResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        rate_card_id: str,
        subject_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineCreateResponse:
        """
        Create Subscription Timeline

        Args:
          rate_card_id: The ID of the rate card to create the subscription timeline for.

          subject_id: The ID of the subject to create the subscription timeline for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/subscription-timelines",
            body=maybe_transform(
                {
                    "rate_card_id": rate_card_id,
                    "subject_id": subject_id,
                },
                subscription_timeline_create_params.SubscriptionTimelineCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineCreateResponse,
        )

    def retrieve(
        self,
        subscription_timeline_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineRetrieveResponse:
        """
        Get Subscription Timeline

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not subscription_timeline_id:
            raise ValueError(
                f"Expected a non-empty value for `subscription_timeline_id` but received {subscription_timeline_id!r}"
            )
        return self._get(
            f"/subscription-timelines/{subscription_timeline_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineRetrieveResponse,
        )

    def list(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineListResponse:
        """
        List Subscription Timelines

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/subscription-timelines",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    subscription_timeline_list_params.SubscriptionTimelineListParams,
                ),
            ),
            cast_to=SubscriptionTimelineListResponse,
        )

    def start(
        self,
        subscription_timeline_id: str,
        *,
        checkout_callback_urls: CheckoutCallbackParam,
        create_checkout_session: Literal["when_required", "always"],
        effective_at: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineStartResponse:
        """
        Start Subscription Timeline

        Args:
          checkout_callback_urls: The URLs to redirect to after the checkout is completed or cancelled, if a
              checkout is required.

          create_checkout_session: Determines whether a checkout session is always required even if the subject has
              a payment method on file. By default, if the subject has a payment method on
              file, the subscription will be created and billed for immediately.

          effective_at: When the subscription should become active. If not provided, the current date
              and time will be used.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not subscription_timeline_id:
            raise ValueError(
                f"Expected a non-empty value for `subscription_timeline_id` but received {subscription_timeline_id!r}"
            )
        return self._post(
            f"/subscription-timelines/{subscription_timeline_id}/start",
            body=maybe_transform(
                {
                    "checkout_callback_urls": checkout_callback_urls,
                    "create_checkout_session": create_checkout_session,
                    "effective_at": effective_at,
                },
                subscription_timeline_start_params.SubscriptionTimelineStartParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineStartResponse,
        )


class AsyncSubscriptionTimelinesResource(AsyncAPIResource):
    @cached_property
    def items(self) -> AsyncItemsResource:
        return AsyncItemsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSubscriptionTimelinesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/uselark/lark-billing-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSubscriptionTimelinesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSubscriptionTimelinesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/uselark/lark-billing-python#with_streaming_response
        """
        return AsyncSubscriptionTimelinesResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        rate_card_id: str,
        subject_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineCreateResponse:
        """
        Create Subscription Timeline

        Args:
          rate_card_id: The ID of the rate card to create the subscription timeline for.

          subject_id: The ID of the subject to create the subscription timeline for.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/subscription-timelines",
            body=await async_maybe_transform(
                {
                    "rate_card_id": rate_card_id,
                    "subject_id": subject_id,
                },
                subscription_timeline_create_params.SubscriptionTimelineCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineCreateResponse,
        )

    async def retrieve(
        self,
        subscription_timeline_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineRetrieveResponse:
        """
        Get Subscription Timeline

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not subscription_timeline_id:
            raise ValueError(
                f"Expected a non-empty value for `subscription_timeline_id` but received {subscription_timeline_id!r}"
            )
        return await self._get(
            f"/subscription-timelines/{subscription_timeline_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineRetrieveResponse,
        )

    async def list(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineListResponse:
        """
        List Subscription Timelines

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/subscription-timelines",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    subscription_timeline_list_params.SubscriptionTimelineListParams,
                ),
            ),
            cast_to=SubscriptionTimelineListResponse,
        )

    async def start(
        self,
        subscription_timeline_id: str,
        *,
        checkout_callback_urls: CheckoutCallbackParam,
        create_checkout_session: Literal["when_required", "always"],
        effective_at: Union[str, datetime] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SubscriptionTimelineStartResponse:
        """
        Start Subscription Timeline

        Args:
          checkout_callback_urls: The URLs to redirect to after the checkout is completed or cancelled, if a
              checkout is required.

          create_checkout_session: Determines whether a checkout session is always required even if the subject has
              a payment method on file. By default, if the subject has a payment method on
              file, the subscription will be created and billed for immediately.

          effective_at: When the subscription should become active. If not provided, the current date
              and time will be used.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not subscription_timeline_id:
            raise ValueError(
                f"Expected a non-empty value for `subscription_timeline_id` but received {subscription_timeline_id!r}"
            )
        return await self._post(
            f"/subscription-timelines/{subscription_timeline_id}/start",
            body=await async_maybe_transform(
                {
                    "checkout_callback_urls": checkout_callback_urls,
                    "create_checkout_session": create_checkout_session,
                    "effective_at": effective_at,
                },
                subscription_timeline_start_params.SubscriptionTimelineStartParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SubscriptionTimelineStartResponse,
        )


class SubscriptionTimelinesResourceWithRawResponse:
    def __init__(self, subscription_timelines: SubscriptionTimelinesResource) -> None:
        self._subscription_timelines = subscription_timelines

        self.create = to_raw_response_wrapper(
            subscription_timelines.create,
        )
        self.retrieve = to_raw_response_wrapper(
            subscription_timelines.retrieve,
        )
        self.list = to_raw_response_wrapper(
            subscription_timelines.list,
        )
        self.start = to_raw_response_wrapper(
            subscription_timelines.start,
        )

    @cached_property
    def items(self) -> ItemsResourceWithRawResponse:
        return ItemsResourceWithRawResponse(self._subscription_timelines.items)


class AsyncSubscriptionTimelinesResourceWithRawResponse:
    def __init__(self, subscription_timelines: AsyncSubscriptionTimelinesResource) -> None:
        self._subscription_timelines = subscription_timelines

        self.create = async_to_raw_response_wrapper(
            subscription_timelines.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            subscription_timelines.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            subscription_timelines.list,
        )
        self.start = async_to_raw_response_wrapper(
            subscription_timelines.start,
        )

    @cached_property
    def items(self) -> AsyncItemsResourceWithRawResponse:
        return AsyncItemsResourceWithRawResponse(self._subscription_timelines.items)


class SubscriptionTimelinesResourceWithStreamingResponse:
    def __init__(self, subscription_timelines: SubscriptionTimelinesResource) -> None:
        self._subscription_timelines = subscription_timelines

        self.create = to_streamed_response_wrapper(
            subscription_timelines.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            subscription_timelines.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            subscription_timelines.list,
        )
        self.start = to_streamed_response_wrapper(
            subscription_timelines.start,
        )

    @cached_property
    def items(self) -> ItemsResourceWithStreamingResponse:
        return ItemsResourceWithStreamingResponse(self._subscription_timelines.items)


class AsyncSubscriptionTimelinesResourceWithStreamingResponse:
    def __init__(self, subscription_timelines: AsyncSubscriptionTimelinesResource) -> None:
        self._subscription_timelines = subscription_timelines

        self.create = async_to_streamed_response_wrapper(
            subscription_timelines.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            subscription_timelines.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            subscription_timelines.list,
        )
        self.start = async_to_streamed_response_wrapper(
            subscription_timelines.start,
        )

    @cached_property
    def items(self) -> AsyncItemsResourceWithStreamingResponse:
        return AsyncItemsResourceWithStreamingResponse(self._subscription_timelines.items)
