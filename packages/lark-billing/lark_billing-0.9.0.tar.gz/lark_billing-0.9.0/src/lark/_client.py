# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import LarkError, APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import (
        invoices,
        subjects,
        rate_cards,
        usage_events,
        rate_catalogs,
        subscriptions,
        customer_access,
        customer_portal,
        pricing_metrics,
        subscription_timelines,
    )
    from .resources.invoices import InvoicesResource, AsyncInvoicesResource
    from .resources.subjects import SubjectsResource, AsyncSubjectsResource
    from .resources.rate_cards import RateCardsResource, AsyncRateCardsResource
    from .resources.usage_events import UsageEventsResource, AsyncUsageEventsResource
    from .resources.rate_catalogs import RateCatalogsResource, AsyncRateCatalogsResource
    from .resources.subscriptions import SubscriptionsResource, AsyncSubscriptionsResource
    from .resources.customer_access import CustomerAccessResource, AsyncCustomerAccessResource
    from .resources.customer_portal import CustomerPortalResource, AsyncCustomerPortalResource
    from .resources.pricing_metrics import PricingMetricsResource, AsyncPricingMetricsResource
    from .resources.subscription_timelines.subscription_timelines import (
        SubscriptionTimelinesResource,
        AsyncSubscriptionTimelinesResource,
    )

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Lark", "AsyncLark", "Client", "AsyncClient"]


class Lark(SyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Lark client instance.

        This automatically infers the `api_key` argument from the `LARK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("LARK_API_KEY")
        if api_key is None:
            raise LarkError(
                "The api_key client option must be set either by passing api_key to the client or by setting the LARK_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("LARK_BASE_URL")
        if base_url is None:
            base_url = f"https://api.uselark.ai"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def customer_portal(self) -> CustomerPortalResource:
        from .resources.customer_portal import CustomerPortalResource

        return CustomerPortalResource(self)

    @cached_property
    def rate_cards(self) -> RateCardsResource:
        from .resources.rate_cards import RateCardsResource

        return RateCardsResource(self)

    @cached_property
    def usage_events(self) -> UsageEventsResource:
        from .resources.usage_events import UsageEventsResource

        return UsageEventsResource(self)

    @cached_property
    def subscriptions(self) -> SubscriptionsResource:
        from .resources.subscriptions import SubscriptionsResource

        return SubscriptionsResource(self)

    @cached_property
    def subjects(self) -> SubjectsResource:
        from .resources.subjects import SubjectsResource

        return SubjectsResource(self)

    @cached_property
    def pricing_metrics(self) -> PricingMetricsResource:
        from .resources.pricing_metrics import PricingMetricsResource

        return PricingMetricsResource(self)

    @cached_property
    def customer_access(self) -> CustomerAccessResource:
        from .resources.customer_access import CustomerAccessResource

        return CustomerAccessResource(self)

    @cached_property
    def invoices(self) -> InvoicesResource:
        from .resources.invoices import InvoicesResource

        return InvoicesResource(self)

    @cached_property
    def rate_catalogs(self) -> RateCatalogsResource:
        from .resources.rate_catalogs import RateCatalogsResource

        return RateCatalogsResource(self)

    @cached_property
    def subscription_timelines(self) -> SubscriptionTimelinesResource:
        from .resources.subscription_timelines import SubscriptionTimelinesResource

        return SubscriptionTimelinesResource(self)

    @cached_property
    def with_raw_response(self) -> LarkWithRawResponse:
        return LarkWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LarkWithStreamedResponse:
        return LarkWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"X-API-Key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncLark(AsyncAPIClient):
    # client options
    api_key: str

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncLark client instance.

        This automatically infers the `api_key` argument from the `LARK_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("LARK_API_KEY")
        if api_key is None:
            raise LarkError(
                "The api_key client option must be set either by passing api_key to the client or by setting the LARK_API_KEY environment variable"
            )
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("LARK_BASE_URL")
        if base_url is None:
            base_url = f"https://api.uselark.ai"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def customer_portal(self) -> AsyncCustomerPortalResource:
        from .resources.customer_portal import AsyncCustomerPortalResource

        return AsyncCustomerPortalResource(self)

    @cached_property
    def rate_cards(self) -> AsyncRateCardsResource:
        from .resources.rate_cards import AsyncRateCardsResource

        return AsyncRateCardsResource(self)

    @cached_property
    def usage_events(self) -> AsyncUsageEventsResource:
        from .resources.usage_events import AsyncUsageEventsResource

        return AsyncUsageEventsResource(self)

    @cached_property
    def subscriptions(self) -> AsyncSubscriptionsResource:
        from .resources.subscriptions import AsyncSubscriptionsResource

        return AsyncSubscriptionsResource(self)

    @cached_property
    def subjects(self) -> AsyncSubjectsResource:
        from .resources.subjects import AsyncSubjectsResource

        return AsyncSubjectsResource(self)

    @cached_property
    def pricing_metrics(self) -> AsyncPricingMetricsResource:
        from .resources.pricing_metrics import AsyncPricingMetricsResource

        return AsyncPricingMetricsResource(self)

    @cached_property
    def customer_access(self) -> AsyncCustomerAccessResource:
        from .resources.customer_access import AsyncCustomerAccessResource

        return AsyncCustomerAccessResource(self)

    @cached_property
    def invoices(self) -> AsyncInvoicesResource:
        from .resources.invoices import AsyncInvoicesResource

        return AsyncInvoicesResource(self)

    @cached_property
    def rate_catalogs(self) -> AsyncRateCatalogsResource:
        from .resources.rate_catalogs import AsyncRateCatalogsResource

        return AsyncRateCatalogsResource(self)

    @cached_property
    def subscription_timelines(self) -> AsyncSubscriptionTimelinesResource:
        from .resources.subscription_timelines import AsyncSubscriptionTimelinesResource

        return AsyncSubscriptionTimelinesResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncLarkWithRawResponse:
        return AsyncLarkWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLarkWithStreamedResponse:
        return AsyncLarkWithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        return {"X-API-Key": api_key}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class LarkWithRawResponse:
    _client: Lark

    def __init__(self, client: Lark) -> None:
        self._client = client

    @cached_property
    def customer_portal(self) -> customer_portal.CustomerPortalResourceWithRawResponse:
        from .resources.customer_portal import CustomerPortalResourceWithRawResponse

        return CustomerPortalResourceWithRawResponse(self._client.customer_portal)

    @cached_property
    def rate_cards(self) -> rate_cards.RateCardsResourceWithRawResponse:
        from .resources.rate_cards import RateCardsResourceWithRawResponse

        return RateCardsResourceWithRawResponse(self._client.rate_cards)

    @cached_property
    def usage_events(self) -> usage_events.UsageEventsResourceWithRawResponse:
        from .resources.usage_events import UsageEventsResourceWithRawResponse

        return UsageEventsResourceWithRawResponse(self._client.usage_events)

    @cached_property
    def subscriptions(self) -> subscriptions.SubscriptionsResourceWithRawResponse:
        from .resources.subscriptions import SubscriptionsResourceWithRawResponse

        return SubscriptionsResourceWithRawResponse(self._client.subscriptions)

    @cached_property
    def subjects(self) -> subjects.SubjectsResourceWithRawResponse:
        from .resources.subjects import SubjectsResourceWithRawResponse

        return SubjectsResourceWithRawResponse(self._client.subjects)

    @cached_property
    def pricing_metrics(self) -> pricing_metrics.PricingMetricsResourceWithRawResponse:
        from .resources.pricing_metrics import PricingMetricsResourceWithRawResponse

        return PricingMetricsResourceWithRawResponse(self._client.pricing_metrics)

    @cached_property
    def customer_access(self) -> customer_access.CustomerAccessResourceWithRawResponse:
        from .resources.customer_access import CustomerAccessResourceWithRawResponse

        return CustomerAccessResourceWithRawResponse(self._client.customer_access)

    @cached_property
    def invoices(self) -> invoices.InvoicesResourceWithRawResponse:
        from .resources.invoices import InvoicesResourceWithRawResponse

        return InvoicesResourceWithRawResponse(self._client.invoices)

    @cached_property
    def rate_catalogs(self) -> rate_catalogs.RateCatalogsResourceWithRawResponse:
        from .resources.rate_catalogs import RateCatalogsResourceWithRawResponse

        return RateCatalogsResourceWithRawResponse(self._client.rate_catalogs)

    @cached_property
    def subscription_timelines(self) -> subscription_timelines.SubscriptionTimelinesResourceWithRawResponse:
        from .resources.subscription_timelines import SubscriptionTimelinesResourceWithRawResponse

        return SubscriptionTimelinesResourceWithRawResponse(self._client.subscription_timelines)


class AsyncLarkWithRawResponse:
    _client: AsyncLark

    def __init__(self, client: AsyncLark) -> None:
        self._client = client

    @cached_property
    def customer_portal(self) -> customer_portal.AsyncCustomerPortalResourceWithRawResponse:
        from .resources.customer_portal import AsyncCustomerPortalResourceWithRawResponse

        return AsyncCustomerPortalResourceWithRawResponse(self._client.customer_portal)

    @cached_property
    def rate_cards(self) -> rate_cards.AsyncRateCardsResourceWithRawResponse:
        from .resources.rate_cards import AsyncRateCardsResourceWithRawResponse

        return AsyncRateCardsResourceWithRawResponse(self._client.rate_cards)

    @cached_property
    def usage_events(self) -> usage_events.AsyncUsageEventsResourceWithRawResponse:
        from .resources.usage_events import AsyncUsageEventsResourceWithRawResponse

        return AsyncUsageEventsResourceWithRawResponse(self._client.usage_events)

    @cached_property
    def subscriptions(self) -> subscriptions.AsyncSubscriptionsResourceWithRawResponse:
        from .resources.subscriptions import AsyncSubscriptionsResourceWithRawResponse

        return AsyncSubscriptionsResourceWithRawResponse(self._client.subscriptions)

    @cached_property
    def subjects(self) -> subjects.AsyncSubjectsResourceWithRawResponse:
        from .resources.subjects import AsyncSubjectsResourceWithRawResponse

        return AsyncSubjectsResourceWithRawResponse(self._client.subjects)

    @cached_property
    def pricing_metrics(self) -> pricing_metrics.AsyncPricingMetricsResourceWithRawResponse:
        from .resources.pricing_metrics import AsyncPricingMetricsResourceWithRawResponse

        return AsyncPricingMetricsResourceWithRawResponse(self._client.pricing_metrics)

    @cached_property
    def customer_access(self) -> customer_access.AsyncCustomerAccessResourceWithRawResponse:
        from .resources.customer_access import AsyncCustomerAccessResourceWithRawResponse

        return AsyncCustomerAccessResourceWithRawResponse(self._client.customer_access)

    @cached_property
    def invoices(self) -> invoices.AsyncInvoicesResourceWithRawResponse:
        from .resources.invoices import AsyncInvoicesResourceWithRawResponse

        return AsyncInvoicesResourceWithRawResponse(self._client.invoices)

    @cached_property
    def rate_catalogs(self) -> rate_catalogs.AsyncRateCatalogsResourceWithRawResponse:
        from .resources.rate_catalogs import AsyncRateCatalogsResourceWithRawResponse

        return AsyncRateCatalogsResourceWithRawResponse(self._client.rate_catalogs)

    @cached_property
    def subscription_timelines(self) -> subscription_timelines.AsyncSubscriptionTimelinesResourceWithRawResponse:
        from .resources.subscription_timelines import AsyncSubscriptionTimelinesResourceWithRawResponse

        return AsyncSubscriptionTimelinesResourceWithRawResponse(self._client.subscription_timelines)


class LarkWithStreamedResponse:
    _client: Lark

    def __init__(self, client: Lark) -> None:
        self._client = client

    @cached_property
    def customer_portal(self) -> customer_portal.CustomerPortalResourceWithStreamingResponse:
        from .resources.customer_portal import CustomerPortalResourceWithStreamingResponse

        return CustomerPortalResourceWithStreamingResponse(self._client.customer_portal)

    @cached_property
    def rate_cards(self) -> rate_cards.RateCardsResourceWithStreamingResponse:
        from .resources.rate_cards import RateCardsResourceWithStreamingResponse

        return RateCardsResourceWithStreamingResponse(self._client.rate_cards)

    @cached_property
    def usage_events(self) -> usage_events.UsageEventsResourceWithStreamingResponse:
        from .resources.usage_events import UsageEventsResourceWithStreamingResponse

        return UsageEventsResourceWithStreamingResponse(self._client.usage_events)

    @cached_property
    def subscriptions(self) -> subscriptions.SubscriptionsResourceWithStreamingResponse:
        from .resources.subscriptions import SubscriptionsResourceWithStreamingResponse

        return SubscriptionsResourceWithStreamingResponse(self._client.subscriptions)

    @cached_property
    def subjects(self) -> subjects.SubjectsResourceWithStreamingResponse:
        from .resources.subjects import SubjectsResourceWithStreamingResponse

        return SubjectsResourceWithStreamingResponse(self._client.subjects)

    @cached_property
    def pricing_metrics(self) -> pricing_metrics.PricingMetricsResourceWithStreamingResponse:
        from .resources.pricing_metrics import PricingMetricsResourceWithStreamingResponse

        return PricingMetricsResourceWithStreamingResponse(self._client.pricing_metrics)

    @cached_property
    def customer_access(self) -> customer_access.CustomerAccessResourceWithStreamingResponse:
        from .resources.customer_access import CustomerAccessResourceWithStreamingResponse

        return CustomerAccessResourceWithStreamingResponse(self._client.customer_access)

    @cached_property
    def invoices(self) -> invoices.InvoicesResourceWithStreamingResponse:
        from .resources.invoices import InvoicesResourceWithStreamingResponse

        return InvoicesResourceWithStreamingResponse(self._client.invoices)

    @cached_property
    def rate_catalogs(self) -> rate_catalogs.RateCatalogsResourceWithStreamingResponse:
        from .resources.rate_catalogs import RateCatalogsResourceWithStreamingResponse

        return RateCatalogsResourceWithStreamingResponse(self._client.rate_catalogs)

    @cached_property
    def subscription_timelines(self) -> subscription_timelines.SubscriptionTimelinesResourceWithStreamingResponse:
        from .resources.subscription_timelines import SubscriptionTimelinesResourceWithStreamingResponse

        return SubscriptionTimelinesResourceWithStreamingResponse(self._client.subscription_timelines)


class AsyncLarkWithStreamedResponse:
    _client: AsyncLark

    def __init__(self, client: AsyncLark) -> None:
        self._client = client

    @cached_property
    def customer_portal(self) -> customer_portal.AsyncCustomerPortalResourceWithStreamingResponse:
        from .resources.customer_portal import AsyncCustomerPortalResourceWithStreamingResponse

        return AsyncCustomerPortalResourceWithStreamingResponse(self._client.customer_portal)

    @cached_property
    def rate_cards(self) -> rate_cards.AsyncRateCardsResourceWithStreamingResponse:
        from .resources.rate_cards import AsyncRateCardsResourceWithStreamingResponse

        return AsyncRateCardsResourceWithStreamingResponse(self._client.rate_cards)

    @cached_property
    def usage_events(self) -> usage_events.AsyncUsageEventsResourceWithStreamingResponse:
        from .resources.usage_events import AsyncUsageEventsResourceWithStreamingResponse

        return AsyncUsageEventsResourceWithStreamingResponse(self._client.usage_events)

    @cached_property
    def subscriptions(self) -> subscriptions.AsyncSubscriptionsResourceWithStreamingResponse:
        from .resources.subscriptions import AsyncSubscriptionsResourceWithStreamingResponse

        return AsyncSubscriptionsResourceWithStreamingResponse(self._client.subscriptions)

    @cached_property
    def subjects(self) -> subjects.AsyncSubjectsResourceWithStreamingResponse:
        from .resources.subjects import AsyncSubjectsResourceWithStreamingResponse

        return AsyncSubjectsResourceWithStreamingResponse(self._client.subjects)

    @cached_property
    def pricing_metrics(self) -> pricing_metrics.AsyncPricingMetricsResourceWithStreamingResponse:
        from .resources.pricing_metrics import AsyncPricingMetricsResourceWithStreamingResponse

        return AsyncPricingMetricsResourceWithStreamingResponse(self._client.pricing_metrics)

    @cached_property
    def customer_access(self) -> customer_access.AsyncCustomerAccessResourceWithStreamingResponse:
        from .resources.customer_access import AsyncCustomerAccessResourceWithStreamingResponse

        return AsyncCustomerAccessResourceWithStreamingResponse(self._client.customer_access)

    @cached_property
    def invoices(self) -> invoices.AsyncInvoicesResourceWithStreamingResponse:
        from .resources.invoices import AsyncInvoicesResourceWithStreamingResponse

        return AsyncInvoicesResourceWithStreamingResponse(self._client.invoices)

    @cached_property
    def rate_catalogs(self) -> rate_catalogs.AsyncRateCatalogsResourceWithStreamingResponse:
        from .resources.rate_catalogs import AsyncRateCatalogsResourceWithStreamingResponse

        return AsyncRateCatalogsResourceWithStreamingResponse(self._client.rate_catalogs)

    @cached_property
    def subscription_timelines(self) -> subscription_timelines.AsyncSubscriptionTimelinesResourceWithStreamingResponse:
        from .resources.subscription_timelines import AsyncSubscriptionTimelinesResourceWithStreamingResponse

        return AsyncSubscriptionTimelinesResourceWithStreamingResponse(self._client.subscription_timelines)


Client = Lark

AsyncClient = AsyncLark
