"""
RAG Agent SDK - Python client library for RAG Agent API.

A comprehensive SDK for interacting with RAG Agent (LightRAG-based) services,
providing easy-to-use interfaces for dataset management, document processing,
RAG queries, and knowledge graph operations.

Quick Start:
    ```python
    from rag_agent_sdk import RagAgentClient
    
    # Async client (recommended for production)
    async with RagAgentClient(api_key="your-key") as client:
        response = await client.query.query("dataset-id", "What is RAG?")
        print(response.response)
    
    # Sync client (for simple scripts)
    from rag_agent_sdk import SyncRagAgentClient
    
    with SyncRagAgentClient(api_key="your-key") as client:
        response = client.query.query("dataset-id", "What is RAG?")
        print(response.response)
    ```

Environment Variables:
    RAG_AGENT_BASE_URL: Server URL (default: http://localhost:9621)
    RAG_AGENT_API_KEY: API key for authentication
    RAG_AGENT_TIMEOUT: Request timeout in seconds
    RAG_AGENT_DEBUG: Enable debug logging (true/false)
"""

from .client import RagAgentClient
from .sync_client import SyncRagAgentClient
from .mock import MockRagAgentClient
from .config import SDKConfig, get_default_config
from .logging import configure_logging
from .exceptions import (
    RagAgentError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    ServerError,
    DatasetNotFoundError,
    DocumentNotFoundError,
    ConnectionError,
    TimeoutError,
)
from .models import (
    Dataset,
    Document,
    DocStatus,
    QueryResponse,
    QueryMode,
    InsertResponse,
    KnowledgeGraph,
    Entity,
    Relation,
    CrossDatasetQueryResponse,
    DatasetListResponse,
    DocumentListResponse,
    ScanResponse,
    Message,
    Chunk,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "RagAgentClient",       # Async client
    "SyncRagAgentClient",   # Sync client
    "MockRagAgentClient",   # Mock client for testing
    # Configuration
    "SDKConfig",
    "get_default_config",
    "configure_logging",
    # Exceptions
    "RagAgentError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "ServerError",
    "DatasetNotFoundError",
    "DocumentNotFoundError",
    "ConnectionError",
    "TimeoutError",
    # Models
    "Dataset",
    "Document",
    "DocStatus",
    "QueryResponse",
    "QueryMode",
    "InsertResponse",
    "KnowledgeGraph",
    "Entity",
    "Relation",
    "CrossDatasetQueryResponse",
    "DatasetListResponse",
    "DocumentListResponse",
    "ScanResponse",
    "Message",
    "Chunk",
]


# Convenience function for quick start
def create_client(
    base_url: str = None,
    api_key: str = None,
    **kwargs,
) -> RagAgentClient:
    """Create an async RAG Agent client with sensible defaults.
    
    This is a convenience function that reads configuration from
    environment variables if not explicitly provided.
    
    Args:
        base_url: Server URL (env: RAG_AGENT_BASE_URL)
        api_key: API key (env: RAG_AGENT_API_KEY)
        **kwargs: Additional configuration options
        
    Returns:
        Configured RagAgentClient instance.
        
    Example:
        ```python
        from rag_agent_sdk import create_client
        
        # Uses environment variables
        client = create_client()
        
        # Or with explicit config
        client = create_client(api_key="your-key")
        ```
    """
    config = SDKConfig.from_env(base_url=base_url, api_key=api_key, **kwargs)
    return RagAgentClient(
        base_url=config.base_url,
        api_key=config.api_key,
        jwt_token=config.jwt_token,
        timeout=config.timeout,
        max_retries=config.max_retries,
    )


def create_sync_client(
    base_url: str = None,
    api_key: str = None,
    **kwargs,
) -> SyncRagAgentClient:
    """Create a sync RAG Agent client with sensible defaults.
    
    Args:
        base_url: Server URL (env: RAG_AGENT_BASE_URL)
        api_key: API key (env: RAG_AGENT_API_KEY)
        **kwargs: Additional configuration options
        
    Returns:
        Configured SyncRagAgentClient instance.
    """
    return SyncRagAgentClient(base_url=base_url, api_key=api_key, **kwargs)
