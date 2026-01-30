# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, List, Union, Optional
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from .embedder_config import EmbedderConfig
from .reranker_config import RerankerConfig
from .query_llm_config import QueryLlmConfig
from .retriever_config import RetrieverConfig
from .title_llm_config import TitleLlmConfig
from .model_citation_config import ModelCitationConfig

__all__ = [
    "ConfigRetrieveResponse",
    "AllConfigs",
    "AllConfigsAgentLlm",
    "AllConfigsAgents",
    "AllConfigsDoctagLlm",
    "AllConfigsDoctagLlmDefaultMetadataTag",
    "AllConfigsDoctagLlmDefaultMetadataTagTagType",
    "AllConfigsEvaluatorLlm",
    "AllConfigsKeywordEmbedder",
    "NonDeveloperConfig",
]


class AllConfigsAgentLlm(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    enabled: Optional[bool] = FieldInfo(alias="ENABLED", default=None)
    """Whether to use agent mode for queries."""

    max_char_size_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_SIZE_TO_ANSWER", default=None)
    """Maximum character size for history."""

    max_context_tokens: Optional[int] = FieldInfo(alias="MAX_CONTEXT_TOKENS", default=None)
    """
    Maximum tokens for gathered context (applies to evidence buffer and final
    query).
    """

    max_iterations: Optional[int] = FieldInfo(alias="MAX_ITERATIONS", default=None)
    """Maximum agent loop iterations."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum tokens for planning decisions."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the model to be used."""

    show_interim_steps: Optional[bool] = FieldInfo(alias="SHOW_INTERIM_STEPS", default=None)
    """Whether to show agent's intermediate steps."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)
    """The system instruction for agent planning."""

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Temperature for agent decisions."""


class AllConfigsAgents(BaseModel):
    agent_model_name: Optional[str] = FieldInfo(alias="AGENT_MODEL_NAME", default=None)
    """The name of the model to be used for the agent."""

    agent_prompt: Optional[str] = FieldInfo(alias="AGENT_PROMPT", default=None)

    enabled: Optional[bool] = FieldInfo(alias="ENABLED", default=None)
    """Whether to use agents mode for queries."""

    llm_agent_temperature: Optional[float] = FieldInfo(alias="LLM_AGENT_TEMPERATURE", default=None)
    """Temperature value for randomness."""

    llm_page_filter_model_name: Optional[str] = FieldInfo(alias="LLM_PAGE_FILTER_MODEL_NAME", default=None)
    """The name of the model to be used for the llm page filter model."""

    llm_page_filter_prompt: Optional[str] = FieldInfo(alias="LLM_PAGE_FILTER_PROMPT", default=None)

    llm_page_filter_temperature: Optional[float] = FieldInfo(alias="LLM_PAGE_FILTER_TEMPERATURE", default=None)
    """Temperature value for randomness."""

    llm_summarise_model_name: Optional[str] = FieldInfo(alias="LLM_SUMMARISE_MODEL_NAME", default=None)
    """The name of the model to be used for the llm summarise model."""

    llm_summarise_prompt: Optional[str] = FieldInfo(alias="LLM_SUMMARISE_PROMPT", default=None)

    llm_summarise_temperature: Optional[float] = FieldInfo(alias="LLM_SUMMARISE_TEMPERATURE", default=None)
    """Temperature value for randomness."""


class AllConfigsDoctagLlmDefaultMetadataTagTagType(BaseModel):
    """Tag format configuration stored as JSONB.

    Type-specific fields:
    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """

    options: Optional[List[str]] = None

    type: Optional[Literal["checkbox", "text", "number", "select", "folder", "search", "date"]] = None


class AllConfigsDoctagLlmDefaultMetadataTag(BaseModel):
    """Base template for tag configuration - used for seeding default tags."""

    name: str

    instruction: Optional[str] = None

    tag_type: Optional[AllConfigsDoctagLlmDefaultMetadataTagTagType] = None
    """Tag format configuration stored as JSONB.

    Type-specific fields:

    - select: options (list of choices, can be single or multi-select)
    - search: tag name is the query, chunks include relevance scores
    - checkbox, text, number, folder: type only
    """


class AllConfigsDoctagLlm(BaseModel):
    """
    Configuration for DoctagLLM - extracts information from documents based on tag instructions.
    """

    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    default_metadata_tags: Optional[List[AllConfigsDoctagLlmDefaultMetadataTag]] = FieldInfo(
        alias="DEFAULT_METADATA_TAGS", default=None
    )
    """
    Metadata templates used for automatic document metadata extraction during
    indexing.
    """

    max_char_context_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_CONTEXT_TO_ANSWER", default=None)
    """Maximum characters in document for context."""

    max_concurrent_docs: Optional[int] = FieldInfo(alias="MAX_CONCURRENT_DOCS", default=None)
    """Maximum concurrent documents for doctag generation."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum number of tokens allowed for all answers."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the non-reasoning model to be used."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Temperature for factual answers."""


class AllConfigsEvaluatorLlm(BaseModel):
    api_type: Optional[Literal["local", "remote"]] = FieldInfo(alias="API_TYPE", default=None)
    """The inference type (local or remote)."""

    max_char_size_to_answer: Optional[int] = FieldInfo(alias="MAX_CHAR_SIZE_TO_ANSWER", default=None)
    """Maximum character size for evaluation context."""

    max_tokens: Optional[int] = FieldInfo(alias="MAX_TOKENS", default=None)
    """Maximum tokens for evaluation response."""

    api_model_name: Optional[str] = FieldInfo(alias="MODEL_NAME", default=None)
    """The name of the non-reasoning model to be used."""

    system_instruction: Optional[str] = FieldInfo(alias="SYSTEM_INSTRUCTION", default=None)
    """The system instruction for chunk evaluation."""

    temperature: Optional[float] = FieldInfo(alias="TEMPERATURE", default=None)
    """Low temperature for consistent evaluation."""


class AllConfigsKeywordEmbedder(BaseModel):
    """Configuration for keyword embedder with BM25 scoring."""

    bm25_avgdl: Optional[float] = FieldInfo(alias="BM25_AVGDL", default=None)
    """Average document length in tokens.

    Adjust based on your documents: chat messages ~20-50, articles ~100-300, papers
    ~1000+
    """

    bm25_b: Optional[float] = FieldInfo(alias="BM25_B", default=None)
    """BM25 document length normalization (0.0-1.0).

    0=ignore length, 1=full penalty for long docs. Default 0.75 is standard.
    """

    bm25_k1: Optional[float] = FieldInfo(alias="BM25_K1", default=None)
    """BM25 term frequency saturation (1.2-2.0).

    Higher = more weight on term repetition. Default 1.5 works for most cases.
    """

    dimension_space: Optional[int] = FieldInfo(alias="DIMENSION_SPACE", default=None)
    """Total dimension space for hash trick (1,048,576 dimensions)"""

    filter_stopwords: Optional[bool] = FieldInfo(alias="FILTER_STOPWORDS", default=None)
    """Remove common stopwords to reduce noise"""


class AllConfigs(BaseModel):
    agent_llm: Optional[AllConfigsAgentLlm] = FieldInfo(alias="AgentLLM", default=None)

    agents: Optional[AllConfigsAgents] = FieldInfo(alias="Agents", default=None)

    chunker: Optional[object] = FieldInfo(alias="Chunker", default=None)

    doctag_llm: Optional[AllConfigsDoctagLlm] = FieldInfo(alias="DoctagLLM", default=None)
    """
    Configuration for DoctagLLM - extracts information from documents based on tag
    instructions.
    """

    embedder: Optional[EmbedderConfig] = FieldInfo(alias="Embedder", default=None)

    evaluator_llm: Optional[AllConfigsEvaluatorLlm] = FieldInfo(alias="EvaluatorLLM", default=None)

    keyword_embedder: Optional[AllConfigsKeywordEmbedder] = FieldInfo(alias="KeywordEmbedder", default=None)
    """Configuration for keyword embedder with BM25 scoring."""

    api_model_citation: Optional[ModelCitationConfig] = FieldInfo(alias="ModelCitation", default=None)

    parser: Optional[object] = FieldInfo(alias="Parser", default=None)

    query_llm: Optional[QueryLlmConfig] = FieldInfo(alias="QueryLLM", default=None)

    reranker: Optional[RerankerConfig] = FieldInfo(alias="Reranker", default=None)

    retriever: Optional[RetrieverConfig] = FieldInfo(alias="Retriever", default=None)

    title_llm: Optional[TitleLlmConfig] = FieldInfo(alias="TitleLLM", default=None)


class NonDeveloperConfig(BaseModel):
    """Limited configuration response for non-developer users"""

    agent_llm: Dict[str, bool] = FieldInfo(alias="AgentLLM")

    query_llm: Dict[str, str] = FieldInfo(alias="QueryLLM")


ConfigRetrieveResponse: TypeAlias = Union[AllConfigs, NonDeveloperConfig]
