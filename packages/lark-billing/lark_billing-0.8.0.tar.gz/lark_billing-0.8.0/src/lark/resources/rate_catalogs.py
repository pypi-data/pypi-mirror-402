# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ..types import (
    rate_catalog_list_params,
    rate_catalog_create_params,
    rate_catalog_add_rates_params,
    rate_catalog_list_rates_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.rate_catalog_list_response import RateCatalogListResponse
from ..types.rate_catalog_create_response import RateCatalogCreateResponse
from ..types.rate_catalog_retrieve_response import RateCatalogRetrieveResponse
from ..types.rate_catalog_add_rates_response import RateCatalogAddRatesResponse
from ..types.rate_catalog_list_rates_response import RateCatalogListRatesResponse

__all__ = ["RateCatalogsResource", "AsyncRateCatalogsResource"]


class RateCatalogsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RateCatalogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/uselark/lark-billing-python#accessing-raw-response-data-eg-headers
        """
        return RateCatalogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RateCatalogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/uselark/lark-billing-python#with_streaming_response
        """
        return RateCatalogsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        description: str,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogCreateResponse:
        """
        Create Rate Catalog

        Args:
          description: The description of the catalog.

          name: The name of the catalog.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/rate-catalogs",
            body=maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                rate_catalog_create_params.RateCatalogCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogCreateResponse,
        )

    def retrieve(
        self,
        rate_catalog_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogRetrieveResponse:
        """
        Get Rate Catalog

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return self._get(
            f"/rate-catalogs/{rate_catalog_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogRetrieveResponse,
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
    ) -> RateCatalogListResponse:
        """
        List Rate Catalogs

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/rate-catalogs",
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
                    rate_catalog_list_params.RateCatalogListParams,
                ),
            ),
            cast_to=RateCatalogListResponse,
        )

    def add_rates(
        self,
        rate_catalog_id: str,
        *,
        billing_interval: Literal["monthly", "yearly"],
        fixed_rates: Iterable[rate_catalog_add_rates_params.FixedRate] | Omit = omit,
        usage_based_rates: Iterable[rate_catalog_add_rates_params.UsageBasedRate] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogAddRatesResponse:
        """
        Add Rates To Rate Catalog

        Args:
          billing_interval: How often the customer will be billed for these rates.

          fixed_rates: The fixed rate to create in the catalog.

          usage_based_rates: The usage based rates to create in the catalog.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return self._post(
            f"/rate-catalogs/{rate_catalog_id}/add_rates",
            body=maybe_transform(
                {
                    "billing_interval": billing_interval,
                    "fixed_rates": fixed_rates,
                    "usage_based_rates": usage_based_rates,
                },
                rate_catalog_add_rates_params.RateCatalogAddRatesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogAddRatesResponse,
        )

    def list_rates(
        self,
        rate_catalog_id: str,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogListRatesResponse:
        """
        List Rates In Catalog

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return self._get(
            f"/rate-catalogs/{rate_catalog_id}/rates",
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
                    rate_catalog_list_rates_params.RateCatalogListRatesParams,
                ),
            ),
            cast_to=RateCatalogListRatesResponse,
        )


class AsyncRateCatalogsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRateCatalogsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/uselark/lark-billing-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRateCatalogsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRateCatalogsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/uselark/lark-billing-python#with_streaming_response
        """
        return AsyncRateCatalogsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        description: str,
        name: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogCreateResponse:
        """
        Create Rate Catalog

        Args:
          description: The description of the catalog.

          name: The name of the catalog.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/rate-catalogs",
            body=await async_maybe_transform(
                {
                    "description": description,
                    "name": name,
                },
                rate_catalog_create_params.RateCatalogCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogCreateResponse,
        )

    async def retrieve(
        self,
        rate_catalog_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogRetrieveResponse:
        """
        Get Rate Catalog

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return await self._get(
            f"/rate-catalogs/{rate_catalog_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogRetrieveResponse,
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
    ) -> RateCatalogListResponse:
        """
        List Rate Catalogs

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/rate-catalogs",
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
                    rate_catalog_list_params.RateCatalogListParams,
                ),
            ),
            cast_to=RateCatalogListResponse,
        )

    async def add_rates(
        self,
        rate_catalog_id: str,
        *,
        billing_interval: Literal["monthly", "yearly"],
        fixed_rates: Iterable[rate_catalog_add_rates_params.FixedRate] | Omit = omit,
        usage_based_rates: Iterable[rate_catalog_add_rates_params.UsageBasedRate] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogAddRatesResponse:
        """
        Add Rates To Rate Catalog

        Args:
          billing_interval: How often the customer will be billed for these rates.

          fixed_rates: The fixed rate to create in the catalog.

          usage_based_rates: The usage based rates to create in the catalog.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return await self._post(
            f"/rate-catalogs/{rate_catalog_id}/add_rates",
            body=await async_maybe_transform(
                {
                    "billing_interval": billing_interval,
                    "fixed_rates": fixed_rates,
                    "usage_based_rates": usage_based_rates,
                },
                rate_catalog_add_rates_params.RateCatalogAddRatesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RateCatalogAddRatesResponse,
        )

    async def list_rates(
        self,
        rate_catalog_id: str,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RateCatalogListRatesResponse:
        """
        List Rates In Catalog

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rate_catalog_id:
            raise ValueError(f"Expected a non-empty value for `rate_catalog_id` but received {rate_catalog_id!r}")
        return await self._get(
            f"/rate-catalogs/{rate_catalog_id}/rates",
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
                    rate_catalog_list_rates_params.RateCatalogListRatesParams,
                ),
            ),
            cast_to=RateCatalogListRatesResponse,
        )


class RateCatalogsResourceWithRawResponse:
    def __init__(self, rate_catalogs: RateCatalogsResource) -> None:
        self._rate_catalogs = rate_catalogs

        self.create = to_raw_response_wrapper(
            rate_catalogs.create,
        )
        self.retrieve = to_raw_response_wrapper(
            rate_catalogs.retrieve,
        )
        self.list = to_raw_response_wrapper(
            rate_catalogs.list,
        )
        self.add_rates = to_raw_response_wrapper(
            rate_catalogs.add_rates,
        )
        self.list_rates = to_raw_response_wrapper(
            rate_catalogs.list_rates,
        )


class AsyncRateCatalogsResourceWithRawResponse:
    def __init__(self, rate_catalogs: AsyncRateCatalogsResource) -> None:
        self._rate_catalogs = rate_catalogs

        self.create = async_to_raw_response_wrapper(
            rate_catalogs.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            rate_catalogs.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            rate_catalogs.list,
        )
        self.add_rates = async_to_raw_response_wrapper(
            rate_catalogs.add_rates,
        )
        self.list_rates = async_to_raw_response_wrapper(
            rate_catalogs.list_rates,
        )


class RateCatalogsResourceWithStreamingResponse:
    def __init__(self, rate_catalogs: RateCatalogsResource) -> None:
        self._rate_catalogs = rate_catalogs

        self.create = to_streamed_response_wrapper(
            rate_catalogs.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            rate_catalogs.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            rate_catalogs.list,
        )
        self.add_rates = to_streamed_response_wrapper(
            rate_catalogs.add_rates,
        )
        self.list_rates = to_streamed_response_wrapper(
            rate_catalogs.list_rates,
        )


class AsyncRateCatalogsResourceWithStreamingResponse:
    def __init__(self, rate_catalogs: AsyncRateCatalogsResource) -> None:
        self._rate_catalogs = rate_catalogs

        self.create = async_to_streamed_response_wrapper(
            rate_catalogs.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            rate_catalogs.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            rate_catalogs.list,
        )
        self.add_rates = async_to_streamed_response_wrapper(
            rate_catalogs.add_rates,
        )
        self.list_rates = async_to_streamed_response_wrapper(
            rate_catalogs.list_rates,
        )
