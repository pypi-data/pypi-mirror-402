# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["RetrieverConfigParam"]


class RetrieverConfigParam(TypedDict, total=False):
    group_size: Annotated[int, PropertyInfo(alias="GROUP_SIZE")]
    """Maximum number of chunks per document for retrieval."""

    hybrid_dense_weight: Annotated[float, PropertyInfo(alias="HYBRID_DENSE_WEIGHT")]
    """Weight for dense vectors in hybrid mode"""

    hybrid_reranker_weight: Annotated[float, PropertyInfo(alias="HYBRID_RERANKER_WEIGHT")]
    """Weight for reranker score in hybrid mode score blending (0-1).

    RRF weight = 1 - this value
    """

    hybrid_sparse_weight: Annotated[float, PropertyInfo(alias="HYBRID_SPARSE_WEIGHT")]
    """Weight for sparse vectors in hybrid mode"""

    max_distinct_documents: Annotated[int, PropertyInfo(alias="MAX_DISTINCT_DOCUMENTS")]
    """Maximum number of distinct documents to search for."""

    max_total_chunks_to_retrieve: Annotated[int, PropertyInfo(alias="MAX_TOTAL_CHUNKS_TO_RETRIEVE")]
    """Maximum total number of chunks to retrieve for all documents retrieved."""

    min_retrieval_sim_score: Annotated[float, PropertyInfo(alias="MIN_RETRIEVAL_SIM_SCORE")]
    """Minimum similarity score for retrieval of a chunk."""

    search_mode: Annotated[Literal["semantic", "keyword", "hybrid"], PropertyInfo(alias="SEARCH_MODE")]
    """Search mode: semantic (dense), keyword (sparse), or hybrid"""
