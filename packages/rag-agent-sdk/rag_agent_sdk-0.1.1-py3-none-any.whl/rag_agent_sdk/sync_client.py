"""
RAG Agent SDK - Synchronous Client.

This module provides a synchronous wrapper around the async client
for developers who prefer synchronous code.
"""

import asyncio
from typing import Any, Dict, Iterator, List, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from .client import RagAgentClient
from .config import SDKConfig
from .models import (
    Dataset,
    Document,
    DocStatus,
    InsertResponse,
    DatasetListResponse,
    DocumentListResponse,
    QueryResponse,
    CrossDatasetQueryResponse,
    KnowledgeGraph,
    Entity,
    Relation,
    ScanResponse,
    QueryMode,
)


def _run_async(coro):
    """Run an async coroutine in a synchronous context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, use thread pool
            with ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop, create new one
        return asyncio.run(coro)


class SyncDatasetsClient:
    """Synchronous client for dataset management."""
    
    def __init__(self, async_client: "RagAgentClient"):
        self._async = async_client.datasets
    
    def create(
        self,
        name: str,
        description: Optional[str] = None,
        storage_type: str = "local",
        chunk_engine: str = "token",
        **kwargs,
    ) -> Dataset:
        """Create a new dataset."""
        return _run_async(self._async.create(
            name=name,
            description=description,
            storage_type=storage_type,
            chunk_engine=chunk_engine,
            **kwargs,
        ))
    
    def get(self, dataset_id: str) -> Dataset:
        """Get dataset by ID."""
        return _run_async(self._async.get(dataset_id))
    
    def get_by_name(self, name: str) -> Optional[Dataset]:
        """Get dataset by name."""
        return _run_async(self._async.get_by_name(name))
    
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ) -> DatasetListResponse:
        """List datasets."""
        return _run_async(self._async.list(page=page, page_size=page_size, **kwargs))
    
    def update(self, dataset_id: str, **updates) -> Dataset:
        """Update dataset."""
        return _run_async(self._async.update(dataset_id, **updates))
    
    def delete(self, dataset_id: str) -> Dict[str, str]:
        """Delete dataset."""
        return _run_async(self._async.delete(dataset_id))


class SyncDocumentsClient:
    """Synchronous client for document management."""
    
    def __init__(self, async_client: "RagAgentClient"):
        self._async = async_client.documents
    
    def upload(
        self,
        dataset_id: str,
        file: Union[str, Path, bytes],
        filename: Optional[str] = None,
    ) -> InsertResponse:
        """Upload a document file."""
        return _run_async(self._async.upload(dataset_id, file, filename))
    
    def insert_text(
        self,
        dataset_id: str,
        text: str,
        source: Optional[str] = None,
    ) -> InsertResponse:
        """Insert text content."""
        return _run_async(self._async.insert_text(dataset_id, text, source))
    
    def insert_batch(
        self,
        dataset_id: str,
        texts: List[str],
        sources: Optional[List[str]] = None,
    ) -> InsertResponse:
        """Insert multiple texts."""
        return _run_async(self._async.insert_batch(dataset_id, texts, sources))
    
    def list(
        self,
        dataset_id: str,
        status: Optional[DocStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentListResponse:
        """List documents."""
        return _run_async(self._async.list(dataset_id, status, page, page_size))
    
    def get(self, dataset_id: str, doc_id: str) -> Document:
        """Get document by ID."""
        return _run_async(self._async.get(dataset_id, doc_id))
    
    def get_status(self, dataset_id: str, doc_id: str) -> Document:
        """Get document processing status."""
        return _run_async(self._async.get_status(dataset_id, doc_id))
    
    def delete(self, dataset_id: str, doc_id: str) -> Dict[str, Any]:
        """Delete a document."""
        return _run_async(self._async.delete(dataset_id, doc_id))
    
    def scan(self, dataset_id: str) -> ScanResponse:
        """Scan and index new documents."""
        return _run_async(self._async.scan(dataset_id))
    
    def clear(self, dataset_id: str) -> Dict[str, str]:
        """Clear all documents."""
        return _run_async(self._async.clear(dataset_id))


class SyncQueryClient:
    """Synchronous client for RAG queries."""
    
    def __init__(self, async_client: "RagAgentClient"):
        self._async = async_client.query
    
    def query(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> QueryResponse:
        """Execute a RAG query."""
        return _run_async(self._async.query(dataset_id, query, mode, **kwargs))
    
    def query_stream(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> Iterator[str]:
        """Execute a streaming RAG query.
        
        Yields response chunks as they are generated.
        """
        async def collect_stream():
            chunks = []
            async for chunk in self._async.query_stream(dataset_id, query, mode, **kwargs):
                chunks.append(chunk)
            return chunks
        
        chunks = _run_async(collect_stream())
        for chunk in chunks:
            yield chunk
    
    def cross_dataset_query(
        self,
        query: str,
        dataset_ids: List[str],
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> CrossDatasetQueryResponse:
        """Execute a cross-dataset query."""
        return _run_async(self._async.cross_dataset_query(query, dataset_ids, mode=mode, **kwargs))
    
    def get_context(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> QueryResponse:
        """Get only the retrieved context."""
        return _run_async(self._async.get_context(dataset_id, query, mode, **kwargs))


class SyncGraphClient:
    """Synchronous client for knowledge graph operations."""
    
    def __init__(self, async_client: "RagAgentClient"):
        self._async = async_client.graph
    
    def get_knowledge_graph(
        self,
        dataset_id: str,
        label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ) -> KnowledgeGraph:
        """Get knowledge graph subgraph."""
        return _run_async(self._async.get_knowledge_graph(dataset_id, label, max_depth, max_nodes))
    
    def get_labels(self, dataset_id: str) -> List[str]:
        """Get all graph labels."""
        return _run_async(self._async.get_labels(dataset_id))
    
    def check_entity_exists(self, dataset_id: str, entity_name: str) -> bool:
        """Check if an entity exists."""
        return _run_async(self._async.check_entity_exists(dataset_id, entity_name))
    
    def get_entity(self, dataset_id: str, entity_name: str) -> Optional[Entity]:
        """Get entity by name."""
        return _run_async(self._async.get_entity(dataset_id, entity_name))
    
    def edit_entity(
        self,
        dataset_id: str,
        entity_name: str,
        updated_data: Dict[str, Any],
        allow_rename: bool = False,
    ) -> Dict[str, Any]:
        """Edit an entity."""
        return _run_async(self._async.edit_entity(dataset_id, entity_name, updated_data, allow_rename))
    
    def search_entities(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 10,
    ) -> List[Entity]:
        """Search for entities."""
        return _run_async(self._async.search_entities(dataset_id, query, top_k))


class SyncRagAgentClient:
    """Synchronous client for RAG Agent API.
    
    This is a synchronous wrapper around the async RagAgentClient.
    Use this if you prefer synchronous code or are in a context
    where async is not available.
    
    Example:
        ```python
        from rag_agent_sdk import SyncRagAgentClient
        
        # Initialize (reads from environment if not specified)
        client = SyncRagAgentClient()
        
        # Or with explicit configuration
        client = SyncRagAgentClient(
            base_url="http://localhost:9621",
            api_key="your-api-key"
        )
        
        # Create dataset
        dataset = client.datasets.create(name="my-kb")
        
        # Upload document
        client.documents.upload(dataset.dataset_uuid, "./doc.pdf")
        
        # Query
        response = client.query.query(dataset.dataset_uuid, "What is RAG?")
        print(response.response)
        ```
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        supabase_service_key: Optional[str] = None,
        supabase_access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        debug: bool = False,
        config: Optional[SDKConfig] = None,
        **kwargs,
    ):
        """Initialize synchronous client.
        
        If no parameters are provided, configuration is read from environment variables.
        
        Authentication Methods:
            1. **LightRAG API Key**: ``api_key="key"`` (admin access)
            2. **Supabase Service Key**: ``supabase_service_key="key"`` (admin access)
            3. **Supabase Anon + JWT**: ``supabase_anon_key="key", supabase_access_token="jwt"``
            4. **JWT Token**: ``jwt_token="token"`` (AUTH_ACCOUNTS)
            5. **Username/Password**: ``username="user", password="pass"``
        
        Args:
            base_url: RAG Agent server URL (env: RAG_AGENT_BASE_URL)
            api_key: LightRAG API key (env: RAG_AGENT_API_KEY)
            jwt_token: JWT token (env: RAG_AGENT_JWT_TOKEN)
            supabase_url: Supabase URL (env: RAG_AGENT_SUPABASE_URL)
            supabase_anon_key: Supabase anon key - requires access_token!
            supabase_service_key: Supabase service key (admin access)
            supabase_access_token: Supabase JWT token
            username: Username for password auth
            password: Password for password auth
            timeout: Request timeout (env: RAG_AGENT_TIMEOUT)
            max_retries: Max retries (env: RAG_AGENT_MAX_RETRIES)
            debug: Enable debug mode (env: RAG_AGENT_DEBUG)
            config: Pre-built SDKConfig object
        """
        # Build config from environment with overrides
        if config is None:
            config = SDKConfig.from_env(
                base_url=base_url,
                api_key=api_key,
                jwt_token=jwt_token,
                supabase_url=supabase_url,
                supabase_anon_key=supabase_anon_key,
                supabase_service_key=supabase_service_key,
                supabase_access_token=supabase_access_token,
                username=username,
                password=password,
                timeout=timeout,
                max_retries=max_retries,
                debug=debug,
            )
        
        self._config = config
        
        # Create async client
        self._async_client = RagAgentClient(
            base_url=config.base_url,
            api_key=config.api_key,
            jwt_token=config.jwt_token,
            supabase_url=config.supabase_url,
            supabase_anon_key=config.supabase_anon_key,
            supabase_service_key=config.supabase_service_key,
            supabase_access_token=config.supabase_access_token,
            username=config.username,
            password=config.password,
            timeout=config.timeout,
            max_retries=config.max_retries,
        )
        
        # Initialize sync sub-clients
        self.datasets = SyncDatasetsClient(self._async_client)
        self.documents = SyncDocumentsClient(self._async_client)
        self.query = SyncQueryClient(self._async_client)
        self.graph = SyncGraphClient(self._async_client)
    
    @property
    def base_url(self) -> str:
        """Get the base URL."""
        return self._config.base_url
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return self._config.has_auth()
    
    def health_check(self) -> dict:
        """Check server health."""
        return _run_async(self._async_client.health_check())
    
    def close(self) -> None:
        """Close the client."""
        _run_async(self._async_client.close())
    
    def __enter__(self) -> "SyncRagAgentClient":
        """Context manager entry."""
        return self
    
    def __exit__(self, *args) -> None:
        """Context manager exit."""
        self.close()
