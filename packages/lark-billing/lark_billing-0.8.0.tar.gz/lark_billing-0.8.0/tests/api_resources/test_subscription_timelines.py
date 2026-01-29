# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from lark import Lark, AsyncLark
from lark.types import (
    SubscriptionTimelineListResponse,
    SubscriptionTimelineStartResponse,
    SubscriptionTimelineCreateResponse,
    SubscriptionTimelineRetrieveResponse,
)
from lark._utils import parse_datetime
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSubscriptionTimelines:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        )
        assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Lark) -> None:
        response = client.subscription_timelines.with_raw_response.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = response.parse()
        assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Lark) -> None:
        with client.subscription_timelines.with_streaming_response.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = response.parse()
            assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.retrieve(
            "subscription_timeline_id",
        )
        assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Lark) -> None:
        response = client.subscription_timelines.with_raw_response.retrieve(
            "subscription_timeline_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = response.parse()
        assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Lark) -> None:
        with client.subscription_timelines.with_streaming_response.retrieve(
            "subscription_timeline_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = response.parse()
            assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Lark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            client.subscription_timelines.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.list()
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.list(
            limit=1,
            offset=0,
        )
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Lark) -> None:
        response = client.subscription_timelines.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = response.parse()
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Lark) -> None:
        with client.subscription_timelines.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = response.parse()
            assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        )
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_start_with_all_params(self, client: Lark) -> None:
        subscription_timeline = client.subscription_timelines.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
            effective_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_start(self, client: Lark) -> None:
        response = client.subscription_timelines.with_raw_response.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = response.parse()
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_start(self, client: Lark) -> None:
        with client.subscription_timelines.with_streaming_response.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = response.parse()
            assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_start(self, client: Lark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            client.subscription_timelines.with_raw_response.start(
                subscription_timeline_id="",
                checkout_callback_urls={
                    "cancelled_url": "https://example.com/callback",
                    "success_url": "https://example.com/callback",
                },
                create_checkout_session="when_required",
            )


class TestAsyncSubscriptionTimelines:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        )
        assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.with_raw_response.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = await response.parse()
        assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.with_streaming_response.create(
            rate_card_id="rate_card_id",
            subject_id="subject_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = await response.parse()
            assert_matches_type(SubscriptionTimelineCreateResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.retrieve(
            "subscription_timeline_id",
        )
        assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.with_raw_response.retrieve(
            "subscription_timeline_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = await response.parse()
        assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.with_streaming_response.retrieve(
            "subscription_timeline_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = await response.parse()
            assert_matches_type(SubscriptionTimelineRetrieveResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncLark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            await async_client.subscription_timelines.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.list()
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.list(
            limit=1,
            offset=0,
        )
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = await response.parse()
        assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = await response.parse()
            assert_matches_type(SubscriptionTimelineListResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        )
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_start_with_all_params(self, async_client: AsyncLark) -> None:
        subscription_timeline = await async_client.subscription_timelines.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
            effective_at=parse_datetime("2019-12-27T18:11:19.117Z"),
        )
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_start(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.with_raw_response.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        subscription_timeline = await response.parse()
        assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_start(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.with_streaming_response.start(
            subscription_timeline_id="subscription_timeline_id",
            checkout_callback_urls={
                "cancelled_url": "https://example.com/callback",
                "success_url": "https://example.com/callback",
            },
            create_checkout_session="when_required",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            subscription_timeline = await response.parse()
            assert_matches_type(SubscriptionTimelineStartResponse, subscription_timeline, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_start(self, async_client: AsyncLark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            await async_client.subscription_timelines.with_raw_response.start(
                subscription_timeline_id="",
                checkout_callback_urls={
                    "cancelled_url": "https://example.com/callback",
                    "success_url": "https://example.com/callback",
                },
                create_checkout_session="when_required",
            )
