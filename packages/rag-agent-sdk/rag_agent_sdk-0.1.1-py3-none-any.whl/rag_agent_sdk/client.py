"""
RAG Agent SDK - Main Client.

This module provides the main client class for interacting with RAG Agent API.
"""

from typing import Optional

from .auth import AuthConfig, AuthHandler
from .utils.http import HttpClient
from .datasets import DatasetsClient
from .documents import DocumentsClient
from .query import QueryClient
from .graph import GraphClient


class RagAgentClient:
    """Main client for RAG Agent API.
    
    This is the primary entry point for interacting with the RAG Agent service.
    It provides access to all API functionality through sub-clients.
    
    Example:
        ```python
        from rag_agent_sdk import RagAgentClient
        
        # Initialize with API key
        client = RagAgentClient(
            base_url="http://localhost:9621",
            api_key="your-api-key"
        )
        
        # Create a dataset
        dataset = await client.datasets.create(name="my-dataset")
        
        # Upload a document
        await client.documents.upload(dataset.dataset_uuid, "./doc.pdf")
        
        # Query the dataset
        response = await client.query.query(
            dataset_id=dataset.dataset_uuid,
            query="What is this document about?"
        )
        print(response.response)
        ```
    
    Attributes:
        datasets: Client for dataset management operations.
        documents: Client for document processing operations.
        query: Client for RAG query operations.
        graph: Client for knowledge graph operations.
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:9621",
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        supabase_url: Optional[str] = None,
        supabase_anon_key: Optional[str] = None,
        supabase_service_key: Optional[str] = None,
        supabase_access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        api_key_header: str = "X-API-Key",
    ):
        """Initialize RAG Agent client.
        
        Authentication Methods:
            1. **LightRAG API Key** (admin access):
               ``api_key="your-lightrag-api-key"``
               
            2. **Supabase Service Key** (admin access):
               ``supabase_service_key="your-service-key"``
               
            3. **Supabase Anon Key + JWT** (user-level access):
               ``supabase_anon_key="anon-key", supabase_access_token="jwt-token"``
               Note: anon_key alone will get 401 error!
               
            4. **JWT Token** (AUTH_ACCOUNTS):
               ``jwt_token="your-jwt-token"``
               
            5. **Username/Password**:
               ``username="user", password="pass"``
        
        Args:
            base_url: Base URL of the RAG Agent server.
            api_key: LightRAG API key for admin access.
            jwt_token: Pre-obtained JWT token (AUTH_ACCOUNTS).
            supabase_url: Supabase project URL.
            supabase_anon_key: Supabase anon key (requires access_token).
            supabase_service_key: Supabase service key (admin access).
            supabase_access_token: Supabase JWT token.
            username: Username for password-based authentication.
            password: Password for password-based authentication.
            timeout: Request timeout in seconds (default: 30).
            max_retries: Maximum retry attempts for failed requests (default: 3).
            retry_delay: Initial delay between retries in seconds (default: 1).
            api_key_header: Header name for API key (default: "X-API-Key").
        """
        self._base_url = base_url.rstrip("/")
        
        # Initialize auth configuration
        self._auth_config = AuthConfig(
            api_key=api_key,
            api_key_header=api_key_header,
            jwt_token=jwt_token,
            supabase_url=supabase_url,
            supabase_anon_key=supabase_anon_key,
            supabase_service_key=supabase_service_key,
            supabase_access_token=supabase_access_token,
            username=username,
            password=password,
        )
        
        # Initialize auth handler
        self._auth_handler = AuthHandler(self._auth_config)
        
        # Initialize HTTP client with auth headers
        self._http = _AuthenticatedHttpClient(
            base_url=self._base_url,
            auth_handler=self._auth_handler,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        
        # Set HTTP client on auth handler for login requests
        self._auth_handler.set_http_client(self._http)
        
        # Initialize sub-clients
        self.datasets = DatasetsClient(self._http)
        self.documents = DocumentsClient(self._http)
        self.query = QueryClient(self._http)
        self.graph = GraphClient(self._http)
    
    @property
    def base_url(self) -> str:
        """Get the base URL of the RAG Agent server."""
        return self._base_url
    
    @property
    def is_authenticated(self) -> bool:
        """Check if the client is authenticated."""
        return self._auth_handler.is_authenticated()
    
    async def close(self) -> None:
        """Close the client and release resources.
        
        Should be called when done using the client to properly
        close HTTP connections.
        """
        await self._http.close()
    
    async def __aenter__(self) -> "RagAgentClient":
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()
    
    async def health_check(self) -> dict:
        """Check server health.
        
        Returns:
            Health status information.
        """
        return await self._http.get("/health")
    
    async def get_server_info(self) -> dict:
        """Get server version and configuration info.
        
        Returns:
            Server information including version.
        """
        try:
            return await self._http.get("/")
        except Exception:
            # Fallback to health endpoint
            return await self.health_check()


class _AuthenticatedHttpClient(HttpClient):
    """HTTP client with automatic authentication header injection."""
    
    def __init__(
        self,
        base_url: str,
        auth_handler: AuthHandler,
        **kwargs,
    ):
        super().__init__(base_url, **kwargs)
        self._auth_handler = auth_handler
    
    async def _request_with_retry(self, method: str, path: str, **kwargs):
        """Override to inject auth headers."""
        # Get auth headers
        auth_headers = await self._auth_handler.get_headers()
        
        # Merge with existing headers
        headers = kwargs.pop("headers", None) or {}
        headers.update(auth_headers)
        kwargs["headers"] = headers
        
        return await super()._request_with_retry(method, path, **kwargs)
    
    async def stream(self, path: str, json=None, headers=None):
        """Override to inject auth headers for streaming."""
        auth_headers = await self._auth_handler.get_headers()
        
        merged_headers = headers or {}
        merged_headers.update(auth_headers)
        
        async for chunk in super().stream(path, json=json, headers=merged_headers):
            yield chunk
    
    async def upload_file(self, path: str, file_data: bytes, filename: str, **kwargs):
        """Override to inject auth headers for file upload."""
        auth_headers = await self._auth_handler.get_headers()
        
        headers = kwargs.pop("headers", None) or {}
        headers.update(auth_headers)
        kwargs["headers"] = headers
        
        return await super().upload_file(path, file_data, filename, **kwargs)
