# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable, Optional
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo
from .parser_config_param import ParserConfigParam
from .chunker_config_param import ChunkerConfigParam
from .embedder_config_param import EmbedderConfigParam
from .reranker_config_param import RerankerConfigParam
from .query_llm_config_param import QueryLlmConfigParam
from .retriever_config_param import RetrieverConfigParam
from .title_llm_config_param import TitleLlmConfigParam
from .model_citation_config_param import ModelCitationConfigParam

__all__ = [
    "ConfigCreateParams",
    "AgentLlm",
    "Agents",
    "DoctagLlm",
    "DoctagLlmDefaultMetadataTag",
    "DoctagLlmDefaultMetadataTagTagType",
    "EvaluatorLlm",
    "KeywordEmbedder",
]


class ConfigCreateParams(TypedDict, total=False):
    agent_llm: Annotated[Optional[AgentLlm], PropertyInfo(alias="AgentLLM")]

    agents: Annotated[Optional[Agents], PropertyInfo(alias="Agents")]

    chunker: Annotated[Optional[ChunkerConfigParam], PropertyInfo(alias="Chunker")]

    doctag_llm: Annotated[Optional[DoctagLlm], PropertyInfo(alias="DoctagLLM")]
    """
    Configuration for DoctagLLM - extracts information from documents based on tag
    instructions.
    """

    embedder: Annotated[Optional[EmbedderConfigParam], PropertyInfo(alias="Embedder")]

    evaluator_llm: Annotated[Optional[EvaluatorLlm], PropertyInfo(alias="EvaluatorLLM")]

    keyword_embedder: Annotated[Optional[KeywordEmbedder], PropertyInfo(alias="KeywordEmbedder")]
    """Configuration for keyword embedder with BM25 scoring."""

    model_citation: Annotated[Optional[ModelCitationConfigParam], PropertyInfo(alias="ModelCitation")]

    parent_message_ext_id: Optional[str]

    parser: Annotated[Optional[ParserConfigParam], PropertyInfo(alias="Parser")]

    query_llm: Annotated[Optional[QueryLlmConfigParam], PropertyInfo(alias="QueryLLM")]

    reranker: Annotated[Optional[RerankerConfigParam], PropertyInfo(alias="Reranker")]

    retriever: Annotated[Optional[RetrieverConfigParam], PropertyInfo(alias="Retriever")]

    title: str

    title_llm: Annotated[Optional[TitleLlmConfigParam], PropertyInfo(alias="TitleLLM")]


class AgentLlm(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    enabled: Annotated[bool, PropertyInfo(alias="ENABLED")]
    """Whether to use agent mode for queries."""

    max_char_size_to_answer: Annotated[int, PropertyInfo(alias="MAX_CHAR_SIZE_TO_ANSWER")]
    """Maximum character size for history."""

    max_context_tokens: Annotated[int, PropertyInfo(alias="MAX_CONTEXT_TOKENS")]
    """
    Maximum tokens for gathered context (applies to evidence buffer and final
    query).
    """

    max_iterations: Annotated[int, PropertyInfo(alias="MAX_ITERATIONS")]
    """Maximum agent loop iterations."""

    max_tokens: Annotated[int, PropertyInfo(alias="MAX_TOKENS")]
    """Maximum tokens for planning decisions."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the model to be used."""

    show_interim_steps: Annotated[bool, PropertyInfo(alias="SHOW_INTERIM_STEPS")]
    """Whether to show agent's intermediate steps."""

    system_instruction: Annotated[str, PropertyInfo(alias="SYSTEM_INSTRUCTION")]
    """The system instruction for agent planning."""

    temperature: Annotated[float, PropertyInfo(alias="TEMPERATURE")]
    """Temperature for agent decisions."""


class Agents(TypedDict, total=False):
    agent_model_name: Annotated[str, PropertyInfo(alias="AGENT_MODEL_NAME")]
    """The name of the model to be used for the agent."""

    agent_prompt: Annotated[str, PropertyInfo(alias="AGENT_PROMPT")]

    enabled: Annotated[bool, PropertyInfo(alias="ENABLED")]
    """Whether to use agents mode for queries."""

    llm_agent_temperature: Annotated[float, PropertyInfo(alias="LLM_AGENT_TEMPERATURE")]
    """Temperature value for randomness."""

    llm_page_filter_model_name: Annotated[str, PropertyInfo(alias="LLM_PAGE_FILTER_MODEL_NAME")]
    """The name of the model to be used for the llm page filter model."""

    llm_page_filter_prompt: Annotated[str, PropertyInfo(alias="LLM_PAGE_FILTER_PROMPT")]

    llm_page_filter_temperature: Annotated[float, PropertyInfo(alias="LLM_PAGE_FILTER_TEMPERATURE")]
    """Temperature value for randomness."""

    llm_summarise_model_name: Annotated[str, PropertyInfo(alias="LLM_SUMMARISE_MODEL_NAME")]
    """The name of the model to be used for the llm summarise model."""

    llm_summarise_prompt: Annotated[str, PropertyInfo(alias="LLM_SUMMARISE_PROMPT")]

    llm_summarise_temperature: Annotated[float, PropertyInfo(alias="LLM_SUMMARISE_TEMPERATURE")]
    """Temperature value for randomness."""


class DoctagLlmDefaultMetadataTagTagType(TypedDict, total=False):
    """Tag format configuration stored as JSONB.

    Type-specific fields:
    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """

    options: SequenceNotStr[str]

    type: Literal["checkbox", "text", "number", "select", "folder", "search", "date"]


class DoctagLlmDefaultMetadataTag(TypedDict, total=False):
    """Base template for tag configuration - used for seeding default tags."""

    name: Required[str]

    instruction: Optional[str]

    tag_type: DoctagLlmDefaultMetadataTagTagType
    """Tag format configuration stored as JSONB.

    Type-specific fields:

    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """


class DoctagLlm(TypedDict, total=False):
    """
    Configuration for DoctagLLM - extracts information from documents based on tag instructions.
    """

    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    default_metadata_tags: Annotated[Iterable[DoctagLlmDefaultMetadataTag], PropertyInfo(alias="DEFAULT_METADATA_TAGS")]
    """
    Metadata templates used for automatic document metadata extraction during
    indexing.
    """

    max_char_context_to_answer: Annotated[int, PropertyInfo(alias="MAX_CHAR_CONTEXT_TO_ANSWER")]
    """Maximum characters in document for context."""

    max_concurrent_docs: Annotated[int, PropertyInfo(alias="MAX_CONCURRENT_DOCS")]
    """Maximum concurrent documents for doctag generation."""

    max_tokens: Annotated[int, PropertyInfo(alias="MAX_TOKENS")]
    """Maximum number of tokens allowed for all answers."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the non-reasoning model to be used."""

    system_instruction: Annotated[str, PropertyInfo(alias="SYSTEM_INSTRUCTION")]

    temperature: Annotated[float, PropertyInfo(alias="TEMPERATURE")]
    """Temperature for factual answers."""


class EvaluatorLlm(TypedDict, total=False):
    api_type: Annotated[Literal["local", "remote"], PropertyInfo(alias="API_TYPE")]
    """The inference type (local or remote)."""

    max_char_size_to_answer: Annotated[int, PropertyInfo(alias="MAX_CHAR_SIZE_TO_ANSWER")]
    """Maximum character size for evaluation context."""

    max_tokens: Annotated[int, PropertyInfo(alias="MAX_TOKENS")]
    """Maximum tokens for evaluation response."""

    model_name: Annotated[str, PropertyInfo(alias="MODEL_NAME")]
    """The name of the non-reasoning model to be used."""

    system_instruction: Annotated[str, PropertyInfo(alias="SYSTEM_INSTRUCTION")]
    """The system instruction for chunk evaluation."""

    temperature: Annotated[float, PropertyInfo(alias="TEMPERATURE")]
    """Low temperature for consistent evaluation."""


class KeywordEmbedder(TypedDict, total=False):
    """Configuration for keyword embedder with BM25 scoring."""

    bm25_avgdl: Annotated[float, PropertyInfo(alias="BM25_AVGDL")]
    """Average document length in tokens.

    Adjust based on your documents: chat messages ~20-50, articles ~100-300, papers
    ~1000+
    """

    bm25_b: Annotated[float, PropertyInfo(alias="BM25_B")]
    """BM25 document length normalization (0.0-1.0).

    0=ignore length, 1=full penalty for long docs. Default 0.75 is standard.
    """

    bm25_k1: Annotated[float, PropertyInfo(alias="BM25_K1")]
    """BM25 term frequency saturation (1.2-2.0).

    Higher = more weight on term repetition. Default 1.5 works for most cases.
    """

    dimension_space: Annotated[int, PropertyInfo(alias="DIMENSION_SPACE")]
    """Total dimension space for hash trick (1,048,576 dimensions)"""

    filter_stopwords: Annotated[bool, PropertyInfo(alias="FILTER_STOPWORDS")]
    """Remove common stopwords to reduce noise"""
