"""
RAG Agent SDK Data Models.

This module defines all Pydantic models used for request/response serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class DocStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    MULTIMODAL_PARSING = "multimodal_parsing"
    MULTIMODAL_PROCESSING = "multimodal_processing"


class QueryMode(str, Enum):
    """RAG query mode."""
    LOCAL = "local"
    GLOBAL = "global"
    HYBRID = "hybrid"
    NAIVE = "naive"
    MIX = "mix"
    BYPASS = "bypass"


class StorageType(str, Enum):
    """Dataset storage type."""
    LOCAL = "local"
    SUPABASE = "supabase"
    S3 = "s3"
    ALIYUN_OSS = "aliyun-oss"


class ChunkEngine(str, Enum):
    """Document chunking strategy."""
    TOKEN = "token"
    SENTENCE = "sentence"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


class Visibility(str, Enum):
    """Dataset visibility."""
    PRIVATE = "private"
    PUBLIC = "public"


# ============ Dataset Models ============

class ModelConfig(BaseModel):
    """Dataset-level model configuration."""
    
    class LLMConfig(BaseModel):
        binding: Optional[str] = None
        model: Optional[str] = None
        host: Optional[str] = None
        api_key: Optional[str] = None
        temperature: Optional[float] = None
        max_tokens: Optional[int] = None
    
    class EmbeddingConfig(BaseModel):
        binding: Optional[str] = None
        model: Optional[str] = None
        dim: Optional[int] = None
        host: Optional[str] = None
        api_key: Optional[str] = None
    
    class RerankConfig(BaseModel):
        model: Optional[str] = None
        host: Optional[str] = None
        api_key: Optional[str] = None
        top_n: Optional[int] = None
    
    llm: Optional[LLMConfig] = None
    embedding: Optional[EmbeddingConfig] = None
    rerank: Optional[RerankConfig] = None


class Dataset(BaseModel):
    """Dataset information model."""
    dataset_uuid: str = Field(description="Dataset UUID")
    name: str = Field(description="Dataset name")
    description: Optional[str] = Field(default=None, description="Dataset description")
    rag_type: str = Field(default="rag", description="RAG type")
    workspace: Optional[str] = Field(default=None, description="Workspace identifier")
    namespace_prefix: Optional[str] = Field(default=None, description="Namespace prefix")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Update timestamp")
    status: str = Field(default="active", description="Dataset status")
    storage_type: str = Field(default="local", description="Storage type")
    chunk_engine: str = Field(default="token", description="Chunking strategy")
    schedule: Optional[str] = Field(default=None, description="Schedule configuration")
    args: Dict[str, Any] = Field(default_factory=dict, description="Additional arguments")
    created_by: Optional[str] = Field(default=None, description="Creator identifier")
    owner_id: Optional[str] = Field(default=None, description="Owner identifier")
    visibility: str = Field(default="private", description="Visibility")
    default_permission: str = Field(default="none", description="Default permission")
    user_id: Optional[str] = Field(default=None, description="User ID")


class CreateDatasetRequest(BaseModel):
    """Request model for creating a dataset."""
    name: str = Field(min_length=1, max_length=255, description="Dataset name")
    description: Optional[str] = Field(default=None, max_length=2000)
    rag_type: str = Field(default="rag")
    workspace: Optional[str] = None
    namespace_prefix: Optional[str] = None
    storage_type: str = Field(default="local")
    chunk_engine: str = Field(default="token")
    schedule: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    llm_config: Optional[ModelConfig] = Field(default=None, alias="model_config")
    created_by: Optional[str] = None
    owner_id: Optional[str] = None
    visibility: str = Field(default="private")
    default_permission: str = Field(default="none")


class UpdateDatasetRequest(BaseModel):
    """Request model for updating a dataset."""
    description: Optional[str] = None
    rag_type: Optional[str] = None
    workspace: Optional[str] = None
    namespace_prefix: Optional[str] = None
    status: Optional[str] = None
    storage_type: Optional[str] = None
    chunk_engine: Optional[str] = None
    schedule: Optional[str] = None
    args: Optional[Dict[str, Any]] = None
    owner_id: Optional[str] = None
    visibility: Optional[str] = None
    default_permission: Optional[str] = None


class DatasetListResponse(BaseModel):
    """Response model for dataset list."""
    datasets: List[Dataset]
    total: int
    page: int
    page_size: int


# ============ Document Models ============

class Document(BaseModel):
    """Document information model."""
    id: str = Field(description="Document ID")
    content_summary: Optional[str] = Field(default=None, description="Content summary")
    content_length: int = Field(default=0, description="Content length")
    status: DocStatus = Field(description="Processing status")
    file_path: Optional[str] = Field(default=None, description="Source file path")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Update timestamp")
    chunks_count: Optional[int] = Field(default=None, description="Number of chunks")


class InsertResponse(BaseModel):
    """Response model for document insertion."""
    status: str = Field(description="Operation status")
    message: str = Field(description="Result message")
    track_id: str = Field(description="Tracking ID for monitoring progress")
    doc_id: Optional[str] = Field(default=None, description="Document ID")


class DocumentListResponse(BaseModel):
    """Response model for document list."""
    documents: List[Document]
    total: int
    page: int
    page_size: int


class ScanResponse(BaseModel):
    """Response model for document scanning."""
    status: str
    message: Optional[str] = None
    track_id: str


# ============ Query Models ============

class Message(BaseModel):
    """Conversation message."""
    role: str = Field(description="Role: 'user' or 'assistant'")
    content: str = Field(description="Message content")


class QueryRequest(BaseModel):
    """Request model for RAG query."""
    query: str = Field(min_length=1, description="Query text")
    mode: str = Field(default="mix", description="Query mode")
    only_need_context: Optional[bool] = None
    only_need_prompt: Optional[bool] = None
    response_type: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=100)
    chunk_top_k: Optional[int] = Field(default=None, ge=1, le=100)
    max_entity_tokens: Optional[int] = None
    max_relation_tokens: Optional[int] = None
    max_total_tokens: Optional[int] = None
    conversation_history: Optional[List[Message]] = None
    history_turns: Optional[int] = Field(default=None, ge=0)
    ids: Optional[List[str]] = None
    user_prompt: Optional[str] = None
    enable_rerank: Optional[bool] = None
    image_base64: Optional[str] = None
    image_url: Optional[str] = None


class Entity(BaseModel):
    """Knowledge graph entity."""
    # Support both 'name' and 'entity' field names from backend
    name: Optional[str] = Field(default=None, alias="entity")
    id: Optional[Union[str, int]] = None
    type: Optional[str] = None
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None  # Backend may include source reference
    
    model_config = {"populate_by_name": True, "extra": "allow"}


class Relation(BaseModel):
    """Knowledge graph relation."""
    # Support both 'source/target' and 'entity1/entity2' field names from backend
    source: Optional[str] = Field(default=None, alias="entity1")
    target: Optional[str] = Field(default=None, alias="entity2")
    id: Optional[Union[str, int]] = None
    type: Optional[str] = Field(default=None, alias="relation")
    description: Optional[str] = None
    weight: Optional[float] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    source_id: Optional[str] = None  # Backend may include source reference
    
    model_config = {"populate_by_name": True, "extra": "allow"}


class Chunk(BaseModel):
    """Document chunk."""
    id: Union[str, int]  # Backend may return int or str
    content: str
    doc_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    score: Optional[float] = None


class QueryResponse(BaseModel):
    """Response model for RAG query."""
    response: str = Field(description="Generated response")
    dataset_id: Optional[str] = Field(default=None, description="Dataset ID")
    query_mode: Optional[str] = Field(default=None, description="Query mode used")
    image_description: Optional[str] = Field(default=None, description="Image description")
    entities: Optional[List[Entity]] = Field(default=None, description="Retrieved entities")
    relationships: Optional[List[Relation]] = Field(default=None, description="Retrieved relationships")
    chunks: Optional[List[Chunk]] = Field(default=None, description="Retrieved chunks")


class CrossDatasetQueryRequest(BaseModel):
    """Request model for cross-dataset query."""
    query: str = Field(min_length=1)
    dataset_ids: List[str] = Field(min_length=1, max_length=10)
    document_filters: Optional[Dict[str, List[str]]] = None
    mode: str = Field(default="mix")
    only_need_context: Optional[bool] = None
    top_k: Optional[int] = None
    enable_rerank: Optional[bool] = True
    max_results_per_dataset: Optional[int] = Field(default=20, ge=1, le=100)


class CrossDatasetQueryResponse(BaseModel):
    """Response model for cross-dataset query."""
    response: str
    query: str
    dataset_count: int
    total_chunks: int
    query_mode: str
    dataset_results: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    performance_stats: Optional[Dict[str, Any]] = None


# ============ Graph Models ============

class KnowledgeGraph(BaseModel):
    """Knowledge graph data."""
    nodes: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class EntityUpdateRequest(BaseModel):
    """Request model for updating an entity."""
    entity_name: str
    updated_data: Dict[str, Any]
    allow_rename: bool = False


class RelationUpdateRequest(BaseModel):
    """Request model for updating a relation."""
    source_id: str
    target_id: str
    updated_data: Dict[str, Any]


# ============ Common Models ============

class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    status: str
    message: str
    deleted_id: Optional[str] = None


class PaginationInfo(BaseModel):
    """Pagination information."""
    page: int
    page_size: int
    total: int
    total_pages: int


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    pagination: PaginationInfo
