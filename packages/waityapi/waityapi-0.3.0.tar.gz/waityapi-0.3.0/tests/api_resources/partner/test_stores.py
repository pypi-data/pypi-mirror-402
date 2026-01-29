# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from waityapi import Waity, AsyncWaity
from tests.utils import assert_matches_type
from waityapi.types.partner import (
    Store,
    WaitTime,
    QueueStatus,
    QueueHistory,
    CheckInResponse,
    CheckOutResponse,
    StoreListResponse,
    StoreUpdateQueueResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStores:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Waity) -> None:
        store = client.partner.stores.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(Store, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(Store, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(Store, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Waity) -> None:
        store = client.partner.stores.list()
        assert_matches_type(StoreListResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(StoreListResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(StoreListResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue(self, client: Waity) -> None:
        store = client.partner.stores.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(QueueStatus, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_queue(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(QueueStatus, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_queue(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(QueueStatus, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_queue(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.queue(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_check_in(self, client: Waity) -> None:
        store = client.partner.stores.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_check_in_with_all_params(self, client: Waity) -> None:
        store = client.partner.stores.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            name="name",
            party_size=1,
            phone="phone",
        )
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_queue_check_in(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_queue_check_in(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(CheckInResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_queue_check_in(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.queue_check_in(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_check_out(self, client: Waity) -> None:
        store = client.partner.stores.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_check_out_with_all_params(self, client: Waity) -> None:
        store = client.partner.stores.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            count=1,
        )
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_queue_check_out(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_queue_check_out(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(CheckOutResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_queue_check_out(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.queue_check_out(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_history(self, client: Waity) -> None:
        store = client.partner.stores.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_queue_history_with_all_params(self, client: Waity) -> None:
        store = client.partner.stores.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            days=1,
        )
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_queue_history(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_queue_history(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(QueueHistory, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_queue_history(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.queue_history(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_queue(self, client: Waity) -> None:
        store = client.partner.stores.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_queue_with_all_params(self, client: Waity) -> None:
        store = client.partner.stores.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            queue_length=0,
            status="open",
            wait_minutes=0,
        )
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_queue(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_queue(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_queue(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.update_queue(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_wait_time(self, client: Waity) -> None:
        store = client.partner.stores.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_wait_time_with_all_params(self, client: Waity) -> None:
        store = client.partner.stores.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            queue_length=0,
            wait_minutes=0,
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_wait_time(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_wait_time(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(WaitTime, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_wait_time(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.update_wait_time(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_wait_time(self, client: Waity) -> None:
        store = client.partner.stores.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_wait_time(self, client: Waity) -> None:
        response = client.partner.stores.with_raw_response.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = response.parse()
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_wait_time(self, client: Waity) -> None:
        with client.partner.stores.with_streaming_response.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = response.parse()
            assert_matches_type(WaitTime, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_wait_time(self, client: Waity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.partner.stores.with_raw_response.wait_time(
                "",
            )


class TestAsyncStores:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(Store, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(Store, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.retrieve(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(Store, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.list()
        assert_matches_type(StoreListResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(StoreListResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(StoreListResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(QueueStatus, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_queue(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(QueueStatus, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_queue(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.queue(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(QueueStatus, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_queue(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.queue(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_check_in(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_check_in_with_all_params(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            name="name",
            party_size=1,
            phone="phone",
        )
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_queue_check_in(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(CheckInResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_queue_check_in(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.queue_check_in(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(CheckInResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_queue_check_in(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.queue_check_in(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_check_out(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_check_out_with_all_params(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            count=1,
        )
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_queue_check_out(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(CheckOutResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_queue_check_out(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.queue_check_out(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(CheckOutResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_queue_check_out(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.queue_check_out(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_history(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_queue_history_with_all_params(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            days=1,
        )
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_queue_history(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(QueueHistory, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_queue_history(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.queue_history(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(QueueHistory, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_queue_history(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.queue_history(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_queue(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_queue_with_all_params(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            queue_length=0,
            status="open",
            wait_minutes=0,
        )
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_queue(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_queue(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.update_queue(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(StoreUpdateQueueResponse, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_queue(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.update_queue(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_wait_time(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_wait_time_with_all_params(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
            queue_length=0,
            wait_minutes=0,
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_wait_time(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_wait_time(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.update_wait_time(
            id="589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(WaitTime, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_wait_time(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.update_wait_time(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_wait_time(self, async_client: AsyncWaity) -> None:
        store = await async_client.partner.stores.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_wait_time(self, async_client: AsyncWaity) -> None:
        response = await async_client.partner.stores.with_raw_response.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        store = await response.parse()
        assert_matches_type(WaitTime, store, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_wait_time(self, async_client: AsyncWaity) -> None:
        async with async_client.partner.stores.with_streaming_response.wait_time(
            "589616e0-2a71-4866-9736-78fdf0d64d1d",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            store = await response.parse()
            assert_matches_type(WaitTime, store, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_wait_time(self, async_client: AsyncWaity) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.partner.stores.with_raw_response.wait_time(
                "",
            )
