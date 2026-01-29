# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from lark import Lark, AsyncLark
from lark.types import (
    RateCatalogListResponse,
    RateCatalogCreateResponse,
    RateCatalogAddRatesResponse,
    RateCatalogRetrieveResponse,
    RateCatalogListRatesResponse,
)
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRateCatalogs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.create(
            description="My Catalog Description",
            name="My Catalog",
        )
        assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Lark) -> None:
        response = client.rate_catalogs.with_raw_response.create(
            description="My Catalog Description",
            name="My Catalog",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = response.parse()
        assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Lark) -> None:
        with client.rate_catalogs.with_streaming_response.create(
            description="My Catalog Description",
            name="My Catalog",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = response.parse()
            assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.retrieve(
            "rate_catalog_id",
        )
        assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Lark) -> None:
        response = client.rate_catalogs.with_raw_response.retrieve(
            "rate_catalog_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = response.parse()
        assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Lark) -> None:
        with client.rate_catalogs.with_streaming_response.retrieve(
            "rate_catalog_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = response.parse()
            assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Lark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            client.rate_catalogs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.list()
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.list(
            limit=1,
            offset=0,
        )
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Lark) -> None:
        response = client.rate_catalogs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = response.parse()
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Lark) -> None:
        with client.rate_catalogs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = response.parse()
            assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_rates(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        )
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_add_rates_with_all_params(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
            fixed_rates=[
                {
                    "code": "code",
                    "name": "Base Rate",
                    "price": {
                        "amount": {
                            "currency_code": "usd",
                            "value": "100",
                        },
                        "price_type": "flat",
                    },
                    "description": None,
                }
            ],
            usage_based_rates=[
                {
                    "code": "code",
                    "name": "name",
                    "price": {
                        "amount": {
                            "currency_code": "usd",
                            "value": "2500",
                        },
                        "price_type": "flat",
                    },
                    "pricing_metric_id": "pricing_metric_id",
                    "usage_based_rate_type": "simple",
                    "description": "description",
                    "included_units": 0,
                }
            ],
        )
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_add_rates(self, client: Lark) -> None:
        response = client.rate_catalogs.with_raw_response.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = response.parse()
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_add_rates(self, client: Lark) -> None:
        with client.rate_catalogs.with_streaming_response.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = response.parse()
            assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_add_rates(self, client: Lark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            client.rate_catalogs.with_raw_response.add_rates(
                rate_catalog_id="",
                billing_interval="monthly",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_rates(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.list_rates(
            rate_catalog_id="rate_catalog_id",
        )
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_rates_with_all_params(self, client: Lark) -> None:
        rate_catalog = client.rate_catalogs.list_rates(
            rate_catalog_id="rate_catalog_id",
            limit=1,
            offset=0,
        )
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_rates(self, client: Lark) -> None:
        response = client.rate_catalogs.with_raw_response.list_rates(
            rate_catalog_id="rate_catalog_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = response.parse()
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_rates(self, client: Lark) -> None:
        with client.rate_catalogs.with_streaming_response.list_rates(
            rate_catalog_id="rate_catalog_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = response.parse()
            assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_rates(self, client: Lark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            client.rate_catalogs.with_raw_response.list_rates(
                rate_catalog_id="",
            )


class TestAsyncRateCatalogs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.create(
            description="My Catalog Description",
            name="My Catalog",
        )
        assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncLark) -> None:
        response = await async_client.rate_catalogs.with_raw_response.create(
            description="My Catalog Description",
            name="My Catalog",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = await response.parse()
        assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncLark) -> None:
        async with async_client.rate_catalogs.with_streaming_response.create(
            description="My Catalog Description",
            name="My Catalog",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = await response.parse()
            assert_matches_type(RateCatalogCreateResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.retrieve(
            "rate_catalog_id",
        )
        assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncLark) -> None:
        response = await async_client.rate_catalogs.with_raw_response.retrieve(
            "rate_catalog_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = await response.parse()
        assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncLark) -> None:
        async with async_client.rate_catalogs.with_streaming_response.retrieve(
            "rate_catalog_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = await response.parse()
            assert_matches_type(RateCatalogRetrieveResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncLark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            await async_client.rate_catalogs.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.list()
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.list(
            limit=1,
            offset=0,
        )
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncLark) -> None:
        response = await async_client.rate_catalogs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = await response.parse()
        assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncLark) -> None:
        async with async_client.rate_catalogs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = await response.parse()
            assert_matches_type(RateCatalogListResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_rates(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        )
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_add_rates_with_all_params(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
            fixed_rates=[
                {
                    "code": "code",
                    "name": "Base Rate",
                    "price": {
                        "amount": {
                            "currency_code": "usd",
                            "value": "100",
                        },
                        "price_type": "flat",
                    },
                    "description": None,
                }
            ],
            usage_based_rates=[
                {
                    "code": "code",
                    "name": "name",
                    "price": {
                        "amount": {
                            "currency_code": "usd",
                            "value": "2500",
                        },
                        "price_type": "flat",
                    },
                    "pricing_metric_id": "pricing_metric_id",
                    "usage_based_rate_type": "simple",
                    "description": "description",
                    "included_units": 0,
                }
            ],
        )
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_add_rates(self, async_client: AsyncLark) -> None:
        response = await async_client.rate_catalogs.with_raw_response.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = await response.parse()
        assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_add_rates(self, async_client: AsyncLark) -> None:
        async with async_client.rate_catalogs.with_streaming_response.add_rates(
            rate_catalog_id="rate_catalog_id",
            billing_interval="monthly",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = await response.parse()
            assert_matches_type(RateCatalogAddRatesResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_add_rates(self, async_client: AsyncLark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            await async_client.rate_catalogs.with_raw_response.add_rates(
                rate_catalog_id="",
                billing_interval="monthly",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_rates(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.list_rates(
            rate_catalog_id="rate_catalog_id",
        )
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_rates_with_all_params(self, async_client: AsyncLark) -> None:
        rate_catalog = await async_client.rate_catalogs.list_rates(
            rate_catalog_id="rate_catalog_id",
            limit=1,
            offset=0,
        )
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_rates(self, async_client: AsyncLark) -> None:
        response = await async_client.rate_catalogs.with_raw_response.list_rates(
            rate_catalog_id="rate_catalog_id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rate_catalog = await response.parse()
        assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_rates(self, async_client: AsyncLark) -> None:
        async with async_client.rate_catalogs.with_streaming_response.list_rates(
            rate_catalog_id="rate_catalog_id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rate_catalog = await response.parse()
            assert_matches_type(RateCatalogListRatesResponse, rate_catalog, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_rates(self, async_client: AsyncLark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rate_catalog_id` but received ''"):
            await async_client.rate_catalogs.with_raw_response.list_rates(
                rate_catalog_id="",
            )
