# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .stores import (
    StoresResource,
    AsyncStoresResource,
    StoresResourceWithRawResponse,
    AsyncStoresResourceWithRawResponse,
    StoresResourceWithStreamingResponse,
    AsyncStoresResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["PartnerResource", "AsyncPartnerResource"]


class PartnerResource(SyncAPIResource):
    @cached_property
    def stores(self) -> StoresResource:
        return StoresResource(self._client)

    @cached_property
    def with_raw_response(self) -> PartnerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#accessing-raw-response-data-eg-headers
        """
        return PartnerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PartnerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#with_streaming_response
        """
        return PartnerResourceWithStreamingResponse(self)


class AsyncPartnerResource(AsyncAPIResource):
    @cached_property
    def stores(self) -> AsyncStoresResource:
        return AsyncStoresResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncPartnerResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#accessing-raw-response-data-eg-headers
        """
        return AsyncPartnerResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPartnerResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ImJustRicky/WaitySDK#with_streaming_response
        """
        return AsyncPartnerResourceWithStreamingResponse(self)


class PartnerResourceWithRawResponse:
    def __init__(self, partner: PartnerResource) -> None:
        self._partner = partner

    @cached_property
    def stores(self) -> StoresResourceWithRawResponse:
        return StoresResourceWithRawResponse(self._partner.stores)


class AsyncPartnerResourceWithRawResponse:
    def __init__(self, partner: AsyncPartnerResource) -> None:
        self._partner = partner

    @cached_property
    def stores(self) -> AsyncStoresResourceWithRawResponse:
        return AsyncStoresResourceWithRawResponse(self._partner.stores)


class PartnerResourceWithStreamingResponse:
    def __init__(self, partner: PartnerResource) -> None:
        self._partner = partner

    @cached_property
    def stores(self) -> StoresResourceWithStreamingResponse:
        return StoresResourceWithStreamingResponse(self._partner.stores)


class AsyncPartnerResourceWithStreamingResponse:
    def __init__(self, partner: AsyncPartnerResource) -> None:
        self._partner = partner

    @cached_property
    def stores(self) -> AsyncStoresResourceWithStreamingResponse:
        return AsyncStoresResourceWithStreamingResponse(self._partner.stores)
