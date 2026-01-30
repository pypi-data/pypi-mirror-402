"""
RAG Agent SDK - Documents Client.

This module provides document processing and management functionality.
"""

import os
from pathlib import Path
from typing import Any, BinaryIO, Dict, List, Optional, Union

from .models import (
    Document,
    DocStatus,
    InsertResponse,
    DocumentListResponse,
    ScanResponse,
    DeleteResponse,
)
from .exceptions import DocumentNotFoundError


class DocumentsClient:
    """Client for document management operations.
    
    Provides methods for uploading, inserting, listing, and deleting documents.
    """
    
    def __init__(self, http_client):
        """Initialize documents client.
        
        Args:
            http_client: HTTP client instance for making requests.
        """
        self._http = http_client
    
    async def upload(
        self,
        dataset_id: str,
        file: Union[str, Path, BinaryIO, bytes],
        filename: Optional[str] = None,
    ) -> InsertResponse:
        """Upload a document file to a dataset.
        
        Args:
            dataset_id: Target dataset UUID.
            file: File path, file object, or bytes content.
            filename: Optional filename (required if file is bytes).
            
        Returns:
            Upload response with tracking ID.
            
        Raises:
            ValidationError: If file is invalid.
            RagAgentError: If upload fails.
        """
        # Handle different file input types
        if isinstance(file, (str, Path)):
            file_path = Path(file)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file}")
            filename = filename or file_path.name
            with open(file_path, "rb") as f:
                file_data = f.read()
        elif isinstance(file, bytes):
            file_data = file
            if not filename:
                raise ValueError("filename is required when file is bytes")
        else:
            # Assume file-like object
            file_data = file.read()
            if hasattr(file, "name"):
                filename = filename or os.path.basename(file.name)
            if not filename:
                raise ValueError("filename is required")
        
        response = await self._http.upload_file(
            f"/datasets/{dataset_id}/documents/upload",
            file_data=file_data,
            filename=filename,
        )
        
        return InsertResponse(**response)
    
    async def insert_text(
        self,
        dataset_id: str,
        text: str,
        source: Optional[str] = None,
    ) -> InsertResponse:
        """Insert text content into a dataset.
        
        Args:
            dataset_id: Target dataset UUID.
            text: Text content to insert.
            source: Optional source identifier.
            
        Returns:
            Insert response with tracking ID.
        """
        request_data = {"text": text}
        if source:
            request_data["file_source"] = source
        
        response = await self._http.post(
            f"/datasets/{dataset_id}/documents/text",
            json=request_data,
        )
        
        return InsertResponse(**response)
    
    async def insert_batch(
        self,
        dataset_id: str,
        texts: List[str],
        sources: Optional[List[str]] = None,
    ) -> InsertResponse:
        """Insert multiple texts into a dataset.
        
        Args:
            dataset_id: Target dataset UUID.
            texts: List of text contents to insert.
            sources: Optional list of source identifiers.
            
        Returns:
            Insert response with tracking ID.
        """
        request_data = {"texts": texts}
        if sources:
            request_data["file_sources"] = sources
        
        response = await self._http.post(
            f"/datasets/{dataset_id}/documents/texts",
            json=request_data,
        )
        
        return InsertResponse(**response)
    
    async def list(
        self,
        dataset_id: str,
        status: Optional[DocStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentListResponse:
        """List documents in a dataset.
        
        Args:
            dataset_id: Dataset UUID.
            status: Filter by document status.
            page: Page number (1-indexed).
            page_size: Number of items per page.
            
        Returns:
            Paginated list of documents.
        """
        params = {
            "page": page,
            "page_size": page_size,
        }
        if status:
            params["status"] = status.value if isinstance(status, DocStatus) else status
        
        response = await self._http.get(
            f"/datasets/{dataset_id}/documents",
            params=params,
        )
        
        documents = [Document(**d) for d in response.get("documents", response.get("data", []))]
        return DocumentListResponse(
            documents=documents,
            total=response.get("total", len(documents)),
            page=response.get("page", page),
            page_size=response.get("page_size", page_size),
        )
    
    async def get(self, dataset_id: str, doc_id: str) -> Document:
        """Get document by ID.
        
        Args:
            dataset_id: Dataset UUID.
            doc_id: Document ID.
            
        Returns:
            Document information.
            
        Raises:
            DocumentNotFoundError: If document not found.
        """
        try:
            response = await self._http.get(
                f"/datasets/{dataset_id}/documents/{doc_id}"
            )
            return Document(**response)
        except Exception as e:
            if "not found" in str(e).lower():
                raise DocumentNotFoundError(doc_id, dataset_id)
            raise
    
    async def get_status(self, dataset_id: str, track_id: str) -> Dict[str, Any]:
        """Get document processing status by tracking ID.

        Args:
            dataset_id: Dataset UUID.
            track_id: Tracking ID returned from upload/insert operations.

        Returns:
            Dict containing:
                - track_id: The tracking ID
                - documents: List of documents with status info
                - total_count: Total number of documents
                - status_summary: Count per status (e.g., {"processed": 2, "pending": 1})
        """
        response = await self._http.get(
            f"/datasets/{dataset_id}/track_status/{track_id}"
        )
        return response
    
    async def delete(self, dataset_id: str, doc_id: str) -> DeleteResponse:
        """Delete a document.
        
        Args:
            dataset_id: Dataset UUID.
            doc_id: Document ID.
            
        Returns:
            Deletion status.
            
        Raises:
            DocumentNotFoundError: If document not found.
        """
        response = await self._http.delete(
            f"/datasets/{dataset_id}/documents/{doc_id}"
        )
        return DeleteResponse(**response)
    
    async def delete_batch(
        self,
        dataset_id: str,
        doc_ids: List[str],
    ) -> Dict[str, Any]:
        """Delete multiple documents.
        
        Args:
            dataset_id: Dataset UUID.
            doc_ids: List of document IDs to delete.
            
        Returns:
            Batch deletion result.
        """
        return await self._http.post(
            f"/datasets/{dataset_id}/documents/delete-batch",
            json={"doc_ids": doc_ids},
        )
    
    async def scan(self, dataset_id: str) -> ScanResponse:
        """Scan and index new documents in the dataset.
        
        Args:
            dataset_id: Dataset UUID.
            
        Returns:
            Scan response with tracking ID.
        """
        response = await self._http.post(
            f"/datasets/{dataset_id}/documents/scan"
        )
        return ScanResponse(**response)
    
    async def clear(self, dataset_id: str) -> Dict[str, str]:
        """Clear all documents in a dataset.
        
        Args:
            dataset_id: Dataset UUID.
            
        Returns:
            Clear operation result.
        """
        return await self._http.post(
            f"/datasets/{dataset_id}/documents/clear"
        )
    
    async def upload_remote(
        self,
        dataset_id: str,
        url: str,
        filename: Optional[str] = None,
    ) -> InsertResponse:
        """Upload a document from a remote URL.
        
        Args:
            dataset_id: Target dataset UUID.
            url: Remote file URL.
            filename: Optional filename override.
            
        Returns:
            Upload response with tracking ID.
        """
        request_data = {"url": url}
        if filename:
            request_data["filename"] = filename
        
        response = await self._http.post(
            f"/datasets/{dataset_id}/documents/upload-remote",
            json=request_data,
        )
        
        return InsertResponse(**response)
