# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, SequenceNotStr, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.api import notification_create_params, notification_delete_params, notification_update_params
from ..._base_client import make_request_options
from ...types.api.notification_list_response import NotificationListResponse
from ...types.api.notification_create_response import NotificationCreateResponse
from ...types.api.notification_update_response import NotificationUpdateResponse
from ...types.api.notification_get_schemas_response import NotificationGetSchemasResponse

__all__ = ["NotificationsResource", "AsyncNotificationsResource"]


class NotificationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NotificationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return NotificationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NotificationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return NotificationsResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        messages: Iterable[notification_create_params.Message],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationCreateResponse:
        """
        Send E2E encrypted messages to one or more users.

        Each message is encrypted with the recipient's individual shared key. Creates
        bilateral notifications visible to both sender and recipient. If recipient is
        online via WebSocket, delivers in real-time.

        Returns the created notifications.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/api/notifications/",
            body=maybe_transform({"messages": messages}, notification_create_params.NotificationCreateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationCreateResponse,
        )

    def update(
        self,
        *,
        updates: Iterable[notification_update_params.Update],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationUpdateResponse:
        """
        Bulk update notifications.

        Supports:

        - content: Re-encrypt content (sender OR recipient can do this)
        - read: Mark as read (only recipient can do this)

        Returns the updated notifications.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._patch(
            "/api/notifications/",
            body=maybe_transform({"updates": updates}, notification_update_params.NotificationUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationUpdateResponse,
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
    ) -> NotificationListResponse:
        """
        Retrieve all notifications for the current user.

        Returns notifications ordered by most recent first. Bilateral model: user sees
        notifications they sent OR received. Use POST /notifications/read to mark
        specific notifications as read.
        """
        return self._get(
            "/api/notifications/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationListResponse,
        )

    def delete(
        self,
        *,
        external_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete one or more notifications (bilateral - sender or recipient can delete).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            "/api/notifications/",
            body=maybe_transform({"external_ids": external_ids}, notification_delete_params.NotificationDeleteParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def get_schemas(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationGetSchemasResponse:
        """
        Expose all WebSocket message types in the OpenAPI schema.

        - server_messages: Messages sent from server to client
        - client_messages: Messages sent from client to server

        Frontend can autogenerate TypeScript types from OpenAPI schema components.
        """
        return self._get(
            "/api/notifications/ws-schemas",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationGetSchemasResponse,
        )


class AsyncNotificationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNotificationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncNotificationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNotificationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncNotificationsResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        messages: Iterable[notification_create_params.Message],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationCreateResponse:
        """
        Send E2E encrypted messages to one or more users.

        Each message is encrypted with the recipient's individual shared key. Creates
        bilateral notifications visible to both sender and recipient. If recipient is
        online via WebSocket, delivers in real-time.

        Returns the created notifications.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/api/notifications/",
            body=await async_maybe_transform(
                {"messages": messages}, notification_create_params.NotificationCreateParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationCreateResponse,
        )

    async def update(
        self,
        *,
        updates: Iterable[notification_update_params.Update],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationUpdateResponse:
        """
        Bulk update notifications.

        Supports:

        - content: Re-encrypt content (sender OR recipient can do this)
        - read: Mark as read (only recipient can do this)

        Returns the updated notifications.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._patch(
            "/api/notifications/",
            body=await async_maybe_transform({"updates": updates}, notification_update_params.NotificationUpdateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationUpdateResponse,
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
    ) -> NotificationListResponse:
        """
        Retrieve all notifications for the current user.

        Returns notifications ordered by most recent first. Bilateral model: user sees
        notifications they sent OR received. Use POST /notifications/read to mark
        specific notifications as read.
        """
        return await self._get(
            "/api/notifications/",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationListResponse,
        )

    async def delete(
        self,
        *,
        external_ids: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Delete one or more notifications (bilateral - sender or recipient can delete).

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            "/api/notifications/",
            body=await async_maybe_transform(
                {"external_ids": external_ids}, notification_delete_params.NotificationDeleteParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def get_schemas(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NotificationGetSchemasResponse:
        """
        Expose all WebSocket message types in the OpenAPI schema.

        - server_messages: Messages sent from server to client
        - client_messages: Messages sent from client to server

        Frontend can autogenerate TypeScript types from OpenAPI schema components.
        """
        return await self._get(
            "/api/notifications/ws-schemas",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NotificationGetSchemasResponse,
        )


class NotificationsResourceWithRawResponse:
    def __init__(self, notifications: NotificationsResource) -> None:
        self._notifications = notifications

        self.create = to_raw_response_wrapper(
            notifications.create,
        )
        self.update = to_raw_response_wrapper(
            notifications.update,
        )
        self.list = to_raw_response_wrapper(
            notifications.list,
        )
        self.delete = to_raw_response_wrapper(
            notifications.delete,
        )
        self.get_schemas = to_raw_response_wrapper(
            notifications.get_schemas,
        )


class AsyncNotificationsResourceWithRawResponse:
    def __init__(self, notifications: AsyncNotificationsResource) -> None:
        self._notifications = notifications

        self.create = async_to_raw_response_wrapper(
            notifications.create,
        )
        self.update = async_to_raw_response_wrapper(
            notifications.update,
        )
        self.list = async_to_raw_response_wrapper(
            notifications.list,
        )
        self.delete = async_to_raw_response_wrapper(
            notifications.delete,
        )
        self.get_schemas = async_to_raw_response_wrapper(
            notifications.get_schemas,
        )


class NotificationsResourceWithStreamingResponse:
    def __init__(self, notifications: NotificationsResource) -> None:
        self._notifications = notifications

        self.create = to_streamed_response_wrapper(
            notifications.create,
        )
        self.update = to_streamed_response_wrapper(
            notifications.update,
        )
        self.list = to_streamed_response_wrapper(
            notifications.list,
        )
        self.delete = to_streamed_response_wrapper(
            notifications.delete,
        )
        self.get_schemas = to_streamed_response_wrapper(
            notifications.get_schemas,
        )


class AsyncNotificationsResourceWithStreamingResponse:
    def __init__(self, notifications: AsyncNotificationsResource) -> None:
        self._notifications = notifications

        self.create = async_to_streamed_response_wrapper(
            notifications.create,
        )
        self.update = async_to_streamed_response_wrapper(
            notifications.update,
        )
        self.list = async_to_streamed_response_wrapper(
            notifications.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            notifications.delete,
        )
        self.get_schemas = async_to_streamed_response_wrapper(
            notifications.get_schemas,
        )
