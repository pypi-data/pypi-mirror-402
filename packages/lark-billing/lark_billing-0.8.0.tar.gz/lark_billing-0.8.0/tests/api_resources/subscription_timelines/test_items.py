# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from lark import Lark, AsyncLark
from lark._utils import parse_datetime
from tests.utils import assert_matches_type
from lark.types.subscription_timelines import ItemListResponse, ItemCreateResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestItems:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Lark) -> None:
        item = client.subscription_timelines.items.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        )
        assert_matches_type(ItemCreateResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Lark) -> None:
        response = client.subscription_timelines.items.with_raw_response.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemCreateResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Lark) -> None:
        with client.subscription_timelines.items.with_streaming_response.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemCreateResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_create(self, client: Lark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            client.subscription_timelines.items.with_raw_response.create(
                subscription_timeline_id="",
                items=[
                    {
                        "period": {
                            "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                            "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                        },
                        "subscription_input": {
                            "fixed_rate_quantities": {"foo": 0},
                            "rate_card_id": "rate_card_id",
                            "rate_price_multipliers": {"foo": 0},
                        },
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Lark) -> None:
        item = client.subscription_timelines.items.list(
            subscription_timeline_id="subscription_timeline_id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Lark) -> None:
        item = client.subscription_timelines.items.list(
            subscription_timeline_id="subscription_timeline_id",
            limit=1,
            offset=0,
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Lark) -> None:
        response = client.subscription_timelines.items.with_raw_response.list(
            subscription_timeline_id="subscription_timeline_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Lark) -> None:
        with client.subscription_timelines.items.with_streaming_response.list(
            subscription_timeline_id="subscription_timeline_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Lark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            client.subscription_timelines.items.with_raw_response.list(
                subscription_timeline_id="",
            )


class TestAsyncItems:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncLark) -> None:
        item = await async_client.subscription_timelines.items.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        )
        assert_matches_type(ItemCreateResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.items.with_raw_response.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemCreateResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.items.with_streaming_response.create(
            subscription_timeline_id="subscription_timeline_id",
            items=[
                {
                    "period": {
                        "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                        "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                    },
                    "subscription_input": {
                        "fixed_rate_quantities": {"foo": 0},
                        "rate_card_id": "rate_card_id",
                        "rate_price_multipliers": {"foo": 0},
                    },
                }
            ],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemCreateResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_create(self, async_client: AsyncLark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            await async_client.subscription_timelines.items.with_raw_response.create(
                subscription_timeline_id="",
                items=[
                    {
                        "period": {
                            "end": parse_datetime("2019-12-27T18:11:19.117Z"),
                            "start": parse_datetime("2019-12-27T18:11:19.117Z"),
                        },
                        "subscription_input": {
                            "fixed_rate_quantities": {"foo": 0},
                            "rate_card_id": "rate_card_id",
                            "rate_price_multipliers": {"foo": 0},
                        },
                    }
                ],
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncLark) -> None:
        item = await async_client.subscription_timelines.items.list(
            subscription_timeline_id="subscription_timeline_id",
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncLark) -> None:
        item = await async_client.subscription_timelines.items.list(
            subscription_timeline_id="subscription_timeline_id",
            limit=1,
            offset=0,
        )
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncLark) -> None:
        response = await async_client.subscription_timelines.items.with_raw_response.list(
            subscription_timeline_id="subscription_timeline_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        item = await response.parse()
        assert_matches_type(ItemListResponse, item, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncLark) -> None:
        async with async_client.subscription_timelines.items.with_streaming_response.list(
            subscription_timeline_id="subscription_timeline_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            item = await response.parse()
            assert_matches_type(ItemListResponse, item, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncLark) -> None:
        with pytest.raises(
            ValueError, match=r"Expected a non-empty value for `subscription_timeline_id` but received ''"
        ):
            await async_client.subscription_timelines.items.with_raw_response.list(
                subscription_timeline_id="",
            )
