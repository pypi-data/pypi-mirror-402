"""
RAG Agent SDK - Datasets Client.

This module provides dataset management functionality.
"""

from typing import Any, Dict, List, Optional

from .models import (
    Dataset,
    CreateDatasetRequest,
    UpdateDatasetRequest,
    DatasetListResponse,
    ModelConfig,
)
from .exceptions import DatasetNotFoundError


class DatasetsClient:
    """Client for dataset management operations.
    
    Provides methods for creating, reading, updating, and deleting datasets.
    """
    
    def __init__(self, http_client):
        """Initialize datasets client.
        
        Args:
            http_client: HTTP client instance for making requests.
        """
        self._http = http_client
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        storage_type: str = "local",
        chunk_engine: str = "token",
        rag_type: str = "rag",
        workspace: Optional[str] = None,
        namespace_prefix: Optional[str] = None,
        schedule: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        model_config: Optional[Dict[str, Any]] = None,
        created_by: Optional[str] = None,
        owner_id: Optional[str] = None,
        visibility: str = "private",
        default_permission: str = "none",
    ) -> Dataset:
        """Create a new dataset.
        
        Args:
            name: Dataset name (must be unique).
            description: Optional dataset description.
            storage_type: Storage type ('local', 'supabase', 's3', 'aliyun-oss').
            chunk_engine: Chunking strategy ('token', 'sentence', 'semantic', 'recursive').
            rag_type: RAG type (default: 'rag').
            workspace: Optional workspace identifier.
            namespace_prefix: Optional namespace prefix.
            schedule: Optional schedule configuration.
            args: Additional arguments as dict.
            model_config: Dataset-level model configuration.
            created_by: Creator identifier.
            owner_id: Owner identifier.
            visibility: Dataset visibility ('private', 'public').
            default_permission: Default permission level.
            
        Returns:
            Created dataset information.
            
        Raises:
            ValidationError: If request validation fails.
            RagAgentError: If creation fails.
        """
        request_data = {
            "name": name,
            "storage_type": storage_type,
            "chunk_engine": chunk_engine,
            "rag_type": rag_type,
            "visibility": visibility,
            "default_permission": default_permission,
        }
        
        if description is not None:
            request_data["description"] = description
        if workspace is not None:
            request_data["workspace"] = workspace
        if namespace_prefix is not None:
            request_data["namespace_prefix"] = namespace_prefix
        if schedule is not None:
            request_data["schedule"] = schedule
        if args is not None:
            request_data["args"] = args
        if model_config is not None:
            request_data["model_config"] = model_config
        if created_by is not None:
            request_data["created_by"] = created_by
        if owner_id is not None:
            request_data["owner_id"] = owner_id
        
        response = await self._http.post("/datasets", json=request_data)
        
        dataset_data = response.get("dataset", response)
        return Dataset(**dataset_data)
    
    async def get(self, dataset_id: str) -> Dataset:
        """Get dataset by ID.
        
        Args:
            dataset_id: Dataset UUID.
            
        Returns:
            Dataset information.
            
        Raises:
            DatasetNotFoundError: If dataset not found.
        """
        try:
            response = await self._http.get(f"/datasets/{dataset_id}")
            dataset_data = response.get("dataset", response)
            return Dataset(**dataset_data)
        except Exception as e:
            if "not found" in str(e).lower():
                raise DatasetNotFoundError(dataset_id)
            raise
    
    async def get_by_name(self, name: str) -> Optional[Dataset]:
        """Get dataset by name.
        
        Args:
            name: Dataset name.
            
        Returns:
            Dataset information or None if not found.
        """
        datasets = await self.list(page_size=100)
        for dataset in datasets.datasets:
            if dataset.name == name:
                return dataset
        return None
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        visibility: Optional[str] = None,
        owner_id: Optional[str] = None,
    ) -> DatasetListResponse:
        """List datasets.
        
        Args:
            page: Page number (1-indexed).
            page_size: Number of items per page.
            status: Filter by status.
            visibility: Filter by visibility.
            owner_id: Filter by owner ID.
            
        Returns:
            Paginated list of datasets.
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if status:
            params["status"] = status
        if visibility:
            params["visibility"] = visibility
        if owner_id:
            params["owner_id"] = owner_id
        
        response = await self._http.get("/datasets", params=params)
        
        datasets = [Dataset(**d) for d in response.get("datasets", [])]
        return DatasetListResponse(
            datasets=datasets,
            total=response.get("total", len(datasets)),
            page=response.get("page", page),
            page_size=response.get("page_size", page_size),
        )
    
    async def update(
        self,
        dataset_id: str,
        description: Optional[str] = None,
        rag_type: Optional[str] = None,
        workspace: Optional[str] = None,
        namespace_prefix: Optional[str] = None,
        status: Optional[str] = None,
        storage_type: Optional[str] = None,
        chunk_engine: Optional[str] = None,
        schedule: Optional[str] = None,
        args: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None,
        visibility: Optional[str] = None,
        default_permission: Optional[str] = None,
    ) -> Dataset:
        """Update dataset.
        
        Args:
            dataset_id: Dataset UUID.
            description: New description.
            rag_type: New RAG type.
            workspace: New workspace.
            namespace_prefix: New namespace prefix.
            status: New status.
            storage_type: New storage type.
            chunk_engine: New chunking strategy.
            schedule: New schedule.
            args: New additional arguments.
            owner_id: New owner ID.
            visibility: New visibility.
            default_permission: New default permission.
            
        Returns:
            Updated dataset information.
            
        Raises:
            DatasetNotFoundError: If dataset not found.
        """
        update_data = {}
        
        if description is not None:
            update_data["description"] = description
        if rag_type is not None:
            update_data["rag_type"] = rag_type
        if workspace is not None:
            update_data["workspace"] = workspace
        if namespace_prefix is not None:
            update_data["namespace_prefix"] = namespace_prefix
        if status is not None:
            update_data["status"] = status
        if storage_type is not None:
            update_data["storage_type"] = storage_type
        if chunk_engine is not None:
            update_data["chunk_engine"] = chunk_engine
        if schedule is not None:
            update_data["schedule"] = schedule
        if args is not None:
            update_data["args"] = args
        if owner_id is not None:
            update_data["owner_id"] = owner_id
        if visibility is not None:
            update_data["visibility"] = visibility
        if default_permission is not None:
            update_data["default_permission"] = default_permission
        
        response = await self._http.put(f"/datasets/{dataset_id}", json=update_data)
        
        dataset_data = response.get("dataset", response)
        return Dataset(**dataset_data)
    
    async def delete(self, dataset_id: str) -> Dict[str, str]:
        """Delete dataset.
        
        Args:
            dataset_id: Dataset UUID.
            
        Returns:
            Deletion status information.
            
        Raises:
            DatasetNotFoundError: If dataset not found.
        """
        return await self._http.delete(f"/datasets/{dataset_id}")
    
    async def update_model_config(
        self,
        dataset_id: str,
        model_config: Dict[str, Any],
        force: bool = False,
    ) -> Dataset:
        """Update model configuration for a dataset.
        
        Args:
            dataset_id: Dataset UUID.
            model_config: New model configuration.
            force: Force update even if embedding dimension changes.
            
        Returns:
            Updated dataset information.
        """
        params = {"force": force} if force else None
        response = await self._http.put(
            f"/datasets/{dataset_id}/model-config",
            json=model_config,
            params=params,
        )
        
        dataset_data = response.get("dataset", response)
        return Dataset(**dataset_data)
