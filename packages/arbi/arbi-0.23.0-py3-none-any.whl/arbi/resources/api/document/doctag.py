# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, strip_not_given, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.api.document import (
    doctag_create_params,
    doctag_delete_params,
    doctag_update_params,
    doctag_generate_params,
)
from ....types.api.document.doc_tag_response import DocTagResponse
from ....types.api.document.doctag_create_response import DoctagCreateResponse
from ....types.api.document.doctag_generate_response import DoctagGenerateResponse

__all__ = ["DoctagResource", "AsyncDoctagResource"]


class DoctagResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DoctagResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return DoctagResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DoctagResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return DoctagResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_id: str,
        citations: Optional[Dict[str, doctag_create_params.Citations]] | Omit = omit,
        note: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DoctagCreateResponse:
        """
        Apply a tag to one or more documents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._post(
            "/api/document/doctag",
            body=maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_id": tag_ext_id,
                    "citations": citations,
                    "note": note,
                },
                doctag_create_params.DoctagCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DoctagCreateResponse,
        )

    def update(
        self,
        *,
        doc_ext_id: str,
        tag_ext_id: str,
        citations: Optional[Dict[str, doctag_update_params.Citations]] | Omit = omit,
        note: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DocTagResponse:
        """
        Update a doctag's note or citations.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._patch(
            "/api/document/doctag",
            body=maybe_transform(
                {
                    "doc_ext_id": doc_ext_id,
                    "tag_ext_id": tag_ext_id,
                    "citations": citations,
                    "note": note,
                },
                doctag_update_params.DoctagUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DocTagResponse,
        )

    def delete(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Remove a tag from one or more documents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            "/api/document/doctag",
            body=maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_id": tag_ext_id,
                },
                doctag_delete_params.DoctagDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def generate(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_ids: SequenceNotStr[str],
        config_ext_id: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DoctagGenerateResponse:
        """
        Generate AI annotations for documents using tag instructions.

        Creates doctags with AI-generated notes and citations for each (doc, tag) pair.
        Uses tag name + optional instruction as the question to answer about each
        document.

        Returns 202 Accepted immediately - processing happens in background. WebSocket
        notification sent when complete.

        Args:
          config_ext_id: Configuration to use for LLM

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return self._post(
            "/api/document/doctag/generate",
            body=maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_ids": tag_ext_ids,
                },
                doctag_generate_params.DoctagGenerateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"config_ext_id": config_ext_id}, doctag_generate_params.DoctagGenerateParams),
            ),
            cast_to=DoctagGenerateResponse,
        )


class AsyncDoctagResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDoctagResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#accessing-raw-response-data-eg-headers
        """
        return AsyncDoctagResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDoctagResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/arbitrationcity/arbi-python#with_streaming_response
        """
        return AsyncDoctagResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_id: str,
        citations: Optional[Dict[str, doctag_create_params.Citations]] | Omit = omit,
        note: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DoctagCreateResponse:
        """
        Apply a tag to one or more documents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._post(
            "/api/document/doctag",
            body=await async_maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_id": tag_ext_id,
                    "citations": citations,
                    "note": note,
                },
                doctag_create_params.DoctagCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DoctagCreateResponse,
        )

    async def update(
        self,
        *,
        doc_ext_id: str,
        tag_ext_id: str,
        citations: Optional[Dict[str, doctag_update_params.Citations]] | Omit = omit,
        note: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DocTagResponse:
        """
        Update a doctag's note or citations.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._patch(
            "/api/document/doctag",
            body=await async_maybe_transform(
                {
                    "doc_ext_id": doc_ext_id,
                    "tag_ext_id": tag_ext_id,
                    "citations": citations,
                    "note": note,
                },
                doctag_update_params.DoctagUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DocTagResponse,
        )

    async def delete(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Remove a tag from one or more documents.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            "/api/document/doctag",
            body=await async_maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_id": tag_ext_id,
                },
                doctag_delete_params.DoctagDeleteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def generate(
        self,
        *,
        doc_ext_ids: SequenceNotStr[str],
        tag_ext_ids: SequenceNotStr[str],
        config_ext_id: Optional[str] | Omit = omit,
        workspace_key: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DoctagGenerateResponse:
        """
        Generate AI annotations for documents using tag instructions.

        Creates doctags with AI-generated notes and citations for each (doc, tag) pair.
        Uses tag name + optional instruction as the question to answer about each
        document.

        Returns 202 Accepted immediately - processing happens in background. WebSocket
        notification sent when complete.

        Args:
          config_ext_id: Configuration to use for LLM

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {**strip_not_given({"workspace-key": workspace_key}), **(extra_headers or {})}
        return await self._post(
            "/api/document/doctag/generate",
            body=await async_maybe_transform(
                {
                    "doc_ext_ids": doc_ext_ids,
                    "tag_ext_ids": tag_ext_ids,
                },
                doctag_generate_params.DoctagGenerateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"config_ext_id": config_ext_id}, doctag_generate_params.DoctagGenerateParams
                ),
            ),
            cast_to=DoctagGenerateResponse,
        )


class DoctagResourceWithRawResponse:
    def __init__(self, doctag: DoctagResource) -> None:
        self._doctag = doctag

        self.create = to_raw_response_wrapper(
            doctag.create,
        )
        self.update = to_raw_response_wrapper(
            doctag.update,
        )
        self.delete = to_raw_response_wrapper(
            doctag.delete,
        )
        self.generate = to_raw_response_wrapper(
            doctag.generate,
        )


class AsyncDoctagResourceWithRawResponse:
    def __init__(self, doctag: AsyncDoctagResource) -> None:
        self._doctag = doctag

        self.create = async_to_raw_response_wrapper(
            doctag.create,
        )
        self.update = async_to_raw_response_wrapper(
            doctag.update,
        )
        self.delete = async_to_raw_response_wrapper(
            doctag.delete,
        )
        self.generate = async_to_raw_response_wrapper(
            doctag.generate,
        )


class DoctagResourceWithStreamingResponse:
    def __init__(self, doctag: DoctagResource) -> None:
        self._doctag = doctag

        self.create = to_streamed_response_wrapper(
            doctag.create,
        )
        self.update = to_streamed_response_wrapper(
            doctag.update,
        )
        self.delete = to_streamed_response_wrapper(
            doctag.delete,
        )
        self.generate = to_streamed_response_wrapper(
            doctag.generate,
        )


class AsyncDoctagResourceWithStreamingResponse:
    def __init__(self, doctag: AsyncDoctagResource) -> None:
        self._doctag = doctag

        self.create = async_to_streamed_response_wrapper(
            doctag.create,
        )
        self.update = async_to_streamed_response_wrapper(
            doctag.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            doctag.delete,
        )
        self.generate = async_to_streamed_response_wrapper(
            doctag.generate,
        )
