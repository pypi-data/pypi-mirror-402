# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

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
from ...types.partner import (
    store_update_queue_params,
    store_queue_history_params,
    store_queue_check_in_params,
    store_queue_check_out_params,
    store_update_wait_time_params,
)
from ...types.partner.store import Store
from ...types.partner.wait_time import WaitTime
from ...types.partner.queue_status import QueueStatus
from ...types.partner.queue_history import QueueHistory
from ...types.partner.check_in_response import CheckInResponse
from ...types.partner.check_out_response import CheckOutResponse
from ...types.partner.store_list_response import StoreListResponse
from ...types.partner.store_update_queue_response import StoreUpdateQueueResponse

__all__ = ["StoresResource", "AsyncStoresResource"]


class StoresResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StoresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#accessing-raw-response-data-eg-headers
        """
        return StoresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StoresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#with_streaming_response
        """
        return StoresResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Store:
        """
        Returns details for a specific store.

        Required scope: `stores:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/stores/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Store,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StoreListResponse:
        """
        Returns all stores accessible by the API key.

        Required scope: `stores:read`.
        """
        return self._get(
            "/stores",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StoreListResponse,
        )

    def queue(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueueStatus:
        """
        Returns the current queue status for a store.

        Required scope: `queues:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/stores/{id}/queue",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueueStatus,
        )

    def queue_check_in(
        self,
        id: str,
        *,
        name: str | Omit = omit,
        party_size: int | Omit = omit,
        phone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CheckInResponse:
        """
        Adds a customer to the queue.

        Required scope: `queues:write`.

        Args:
          name: Optional customer name

          party_size: Number of people in party

          phone: Optional phone for notifications

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/stores/{id}/queue/check-in",
            body=maybe_transform(
                {
                    "name": name,
                    "party_size": party_size,
                    "phone": phone,
                },
                store_queue_check_in_params.StoreQueueCheckInParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CheckInResponse,
        )

    def queue_check_out(
        self,
        id: str,
        *,
        count: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CheckOutResponse:
        """
        Removes customers from the queue (marks as served).

        Required scope: `queues:write`.

        Args:
          count: Number of people served

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/stores/{id}/queue/check-out",
            body=maybe_transform({"count": count}, store_queue_check_out_params.StoreQueueCheckOutParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CheckOutResponse,
        )

    def queue_history(
        self,
        id: str,
        *,
        days: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueueHistory:
        """
        Returns historical queue data for a store.

        Required scope: `queues:read`.

        Args:
          days: Number of days of history (max 30).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/stores/{id}/queue/history",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"days": days}, store_queue_history_params.StoreQueueHistoryParams),
            ),
            cast_to=QueueHistory,
        )

    def update_queue(
        self,
        id: str,
        *,
        queue_length: int | Omit = omit,
        status: Literal["open", "closed"] | Omit = omit,
        wait_minutes: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StoreUpdateQueueResponse:
        """
        Updates the queue status for a store (queue length, wait time, open/closed).

        Required scope: `queues:write`.

        Args:
          queue_length: Number of people waiting

          status: Queue status (open or closed)

          wait_minutes: Current estimated wait time

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/stores/{id}/queue",
            body=maybe_transform(
                {
                    "queue_length": queue_length,
                    "status": status,
                    "wait_minutes": wait_minutes,
                },
                store_update_queue_params.StoreUpdateQueueParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StoreUpdateQueueResponse,
        )

    def update_wait_time(
        self,
        id: str,
        *,
        queue_length: int | Omit = omit,
        wait_minutes: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WaitTime:
        """
        Updates the current wait time for a store.

        Required scope: `wait_times:write`.

        Args:
          queue_length: Number of people waiting

          wait_minutes: Current wait time in minutes

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._post(
            f"/stores/{id}/wait-time",
            body=maybe_transform(
                {
                    "queue_length": queue_length,
                    "wait_minutes": wait_minutes,
                },
                store_update_wait_time_params.StoreUpdateWaitTimeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WaitTime,
        )

    def wait_time(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WaitTime:
        """
        Returns the current wait time for a store.

        Required scope: `wait_times:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return self._get(
            f"/stores/{id}/wait-time",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WaitTime,
        )


class AsyncStoresResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStoresResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#accessing-raw-response-data-eg-headers
        """
        return AsyncStoresResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStoresResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#with_streaming_response
        """
        return AsyncStoresResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> Store:
        """
        Returns details for a specific store.

        Required scope: `stores:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/stores/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Store,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StoreListResponse:
        """
        Returns all stores accessible by the API key.

        Required scope: `stores:read`.
        """
        return await self._get(
            "/stores",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StoreListResponse,
        )

    async def queue(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueueStatus:
        """
        Returns the current queue status for a store.

        Required scope: `queues:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/stores/{id}/queue",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=QueueStatus,
        )

    async def queue_check_in(
        self,
        id: str,
        *,
        name: str | Omit = omit,
        party_size: int | Omit = omit,
        phone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CheckInResponse:
        """
        Adds a customer to the queue.

        Required scope: `queues:write`.

        Args:
          name: Optional customer name

          party_size: Number of people in party

          phone: Optional phone for notifications

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/stores/{id}/queue/check-in",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "party_size": party_size,
                    "phone": phone,
                },
                store_queue_check_in_params.StoreQueueCheckInParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CheckInResponse,
        )

    async def queue_check_out(
        self,
        id: str,
        *,
        count: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CheckOutResponse:
        """
        Removes customers from the queue (marks as served).

        Required scope: `queues:write`.

        Args:
          count: Number of people served

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/stores/{id}/queue/check-out",
            body=await async_maybe_transform({"count": count}, store_queue_check_out_params.StoreQueueCheckOutParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CheckOutResponse,
        )

    async def queue_history(
        self,
        id: str,
        *,
        days: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> QueueHistory:
        """
        Returns historical queue data for a store.

        Required scope: `queues:read`.

        Args:
          days: Number of days of history (max 30).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/stores/{id}/queue/history",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"days": days}, store_queue_history_params.StoreQueueHistoryParams),
            ),
            cast_to=QueueHistory,
        )

    async def update_queue(
        self,
        id: str,
        *,
        queue_length: int | Omit = omit,
        status: Literal["open", "closed"] | Omit = omit,
        wait_minutes: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> StoreUpdateQueueResponse:
        """
        Updates the queue status for a store (queue length, wait time, open/closed).

        Required scope: `queues:write`.

        Args:
          queue_length: Number of people waiting

          status: Queue status (open or closed)

          wait_minutes: Current estimated wait time

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/stores/{id}/queue",
            body=await async_maybe_transform(
                {
                    "queue_length": queue_length,
                    "status": status,
                    "wait_minutes": wait_minutes,
                },
                store_update_queue_params.StoreUpdateQueueParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StoreUpdateQueueResponse,
        )

    async def update_wait_time(
        self,
        id: str,
        *,
        queue_length: int | Omit = omit,
        wait_minutes: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WaitTime:
        """
        Updates the current wait time for a store.

        Required scope: `wait_times:write`.

        Args:
          queue_length: Number of people waiting

          wait_minutes: Current wait time in minutes

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._post(
            f"/stores/{id}/wait-time",
            body=await async_maybe_transform(
                {
                    "queue_length": queue_length,
                    "wait_minutes": wait_minutes,
                },
                store_update_wait_time_params.StoreUpdateWaitTimeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WaitTime,
        )

    async def wait_time(
        self,
        id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WaitTime:
        """
        Returns the current wait time for a store.

        Required scope: `wait_times:read`.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not id:
            raise ValueError(f"Expected a non-empty value for `id` but received {id!r}")
        return await self._get(
            f"/stores/{id}/wait-time",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WaitTime,
        )


class StoresResourceWithRawResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores

        self.retrieve = to_raw_response_wrapper(
            stores.retrieve,
        )
        self.list = to_raw_response_wrapper(
            stores.list,
        )
        self.queue = to_raw_response_wrapper(
            stores.queue,
        )
        self.queue_check_in = to_raw_response_wrapper(
            stores.queue_check_in,
        )
        self.queue_check_out = to_raw_response_wrapper(
            stores.queue_check_out,
        )
        self.queue_history = to_raw_response_wrapper(
            stores.queue_history,
        )
        self.update_queue = to_raw_response_wrapper(
            stores.update_queue,
        )
        self.update_wait_time = to_raw_response_wrapper(
            stores.update_wait_time,
        )
        self.wait_time = to_raw_response_wrapper(
            stores.wait_time,
        )


class AsyncStoresResourceWithRawResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores

        self.retrieve = async_to_raw_response_wrapper(
            stores.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            stores.list,
        )
        self.queue = async_to_raw_response_wrapper(
            stores.queue,
        )
        self.queue_check_in = async_to_raw_response_wrapper(
            stores.queue_check_in,
        )
        self.queue_check_out = async_to_raw_response_wrapper(
            stores.queue_check_out,
        )
        self.queue_history = async_to_raw_response_wrapper(
            stores.queue_history,
        )
        self.update_queue = async_to_raw_response_wrapper(
            stores.update_queue,
        )
        self.update_wait_time = async_to_raw_response_wrapper(
            stores.update_wait_time,
        )
        self.wait_time = async_to_raw_response_wrapper(
            stores.wait_time,
        )


class StoresResourceWithStreamingResponse:
    def __init__(self, stores: StoresResource) -> None:
        self._stores = stores

        self.retrieve = to_streamed_response_wrapper(
            stores.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            stores.list,
        )
        self.queue = to_streamed_response_wrapper(
            stores.queue,
        )
        self.queue_check_in = to_streamed_response_wrapper(
            stores.queue_check_in,
        )
        self.queue_check_out = to_streamed_response_wrapper(
            stores.queue_check_out,
        )
        self.queue_history = to_streamed_response_wrapper(
            stores.queue_history,
        )
        self.update_queue = to_streamed_response_wrapper(
            stores.update_queue,
        )
        self.update_wait_time = to_streamed_response_wrapper(
            stores.update_wait_time,
        )
        self.wait_time = to_streamed_response_wrapper(
            stores.wait_time,
        )


class AsyncStoresResourceWithStreamingResponse:
    def __init__(self, stores: AsyncStoresResource) -> None:
        self._stores = stores

        self.retrieve = async_to_streamed_response_wrapper(
            stores.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            stores.list,
        )
        self.queue = async_to_streamed_response_wrapper(
            stores.queue,
        )
        self.queue_check_in = async_to_streamed_response_wrapper(
            stores.queue_check_in,
        )
        self.queue_check_out = async_to_streamed_response_wrapper(
            stores.queue_check_out,
        )
        self.queue_history = async_to_streamed_response_wrapper(
            stores.queue_history,
        )
        self.update_queue = async_to_streamed_response_wrapper(
            stores.update_queue,
        )
        self.update_wait_time = async_to_streamed_response_wrapper(
            stores.update_wait_time,
        )
        self.wait_time = async_to_streamed_response_wrapper(
            stores.wait_time,
        )
