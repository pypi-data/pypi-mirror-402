"""
RAG Agent SDK - Query Client.

This module provides RAG query functionality.
"""

import json
from typing import Any, AsyncIterator, Dict, List, Optional, Union

from .models import (
    QueryRequest,
    QueryResponse,
    CrossDatasetQueryRequest,
    CrossDatasetQueryResponse,
    Message,
    QueryMode,
)


class QueryClient:
    """Client for RAG query operations.
    
    Provides methods for executing RAG queries with various modes.
    """
    
    def __init__(self, http_client):
        """Initialize query client.
        
        Args:
            http_client: HTTP client instance for making requests.
        """
        self._http = http_client
    
    async def query(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        only_need_context: Optional[bool] = None,
        only_need_prompt: Optional[bool] = None,
        response_type: Optional[str] = None,
        top_k: Optional[int] = None,
        chunk_top_k: Optional[int] = None,
        max_entity_tokens: Optional[int] = None,
        max_relation_tokens: Optional[int] = None,
        max_total_tokens: Optional[int] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        history_turns: Optional[int] = None,
        ids: Optional[List[str]] = None,
        user_prompt: Optional[str] = None,
        enable_rerank: Optional[bool] = None,
        image_base64: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> QueryResponse:
        """Execute a RAG query on a dataset.
        
        Args:
            dataset_id: Target dataset UUID.
            query: Query text.
            mode: Query mode ('local', 'global', 'hybrid', 'naive', 'mix', 'bypass').
            only_need_context: Return only retrieved context without generating response.
            only_need_prompt: Return only the generated prompt.
            response_type: Response format type.
            top_k: Number of top items to retrieve.
            chunk_top_k: Number of text chunks to retrieve.
            max_entity_tokens: Max tokens for entity context.
            max_relation_tokens: Max tokens for relation context.
            max_total_tokens: Max total tokens budget.
            conversation_history: Previous conversation messages.
            history_turns: Number of conversation turns to consider.
            ids: List of document IDs to filter.
            user_prompt: Custom user prompt.
            enable_rerank: Enable reranking.
            image_base64: Base64 encoded image for image query.
            image_url: URL of image for image query.
            
        Returns:
            Query response with generated answer and context.
        """
        request_data = {
            "query": query,
            "mode": mode.value if isinstance(mode, QueryMode) else mode,
        }
        
        if only_need_context is not None:
            request_data["only_need_context"] = only_need_context
        if only_need_prompt is not None:
            request_data["only_need_prompt"] = only_need_prompt
        if response_type is not None:
            request_data["response_type"] = response_type
        if top_k is not None:
            request_data["top_k"] = top_k
        if chunk_top_k is not None:
            request_data["chunk_top_k"] = chunk_top_k
        if max_entity_tokens is not None:
            request_data["max_entity_tokens"] = max_entity_tokens
        if max_relation_tokens is not None:
            request_data["max_relation_tokens"] = max_relation_tokens
        if max_total_tokens is not None:
            request_data["max_total_tokens"] = max_total_tokens
        if conversation_history is not None:
            request_data["conversation_history"] = conversation_history
        if history_turns is not None:
            request_data["history_turns"] = history_turns
        if ids is not None:
            request_data["ids"] = ids
        if user_prompt is not None:
            request_data["user_prompt"] = user_prompt
        if enable_rerank is not None:
            request_data["enable_rerank"] = enable_rerank
        if image_base64 is not None:
            request_data["image_base64"] = image_base64
        if image_url is not None:
            request_data["image_url"] = image_url
        
        response = await self._http.post(
            f"/datasets/{dataset_id}/query",
            json=request_data,
        )
        
        return QueryResponse(**response)
    
    async def query_stream(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> AsyncIterator[str]:
        """Execute a streaming RAG query.
        
        Args:
            dataset_id: Target dataset UUID.
            query: Query text.
            mode: Query mode.
            **kwargs: Additional query parameters.
            
        Yields:
            Response chunks as they are generated.
        """
        request_data = {
            "query": query,
            "mode": mode.value if isinstance(mode, QueryMode) else mode,
            **kwargs,
        }
        
        async for line in self._http.stream(
            f"/datasets/{dataset_id}/query/stream",
            json=request_data,
        ):
            try:
                data = json.loads(line)
                if "response" in data:
                    yield data["response"]
                elif "error" in data:
                    raise Exception(data["error"])
            except json.JSONDecodeError:
                yield line
    
    async def cross_dataset_query(
        self,
        query: str,
        dataset_ids: List[str],
        document_filters: Optional[Dict[str, List[str]]] = None,
        mode: Union[str, QueryMode] = "mix",
        only_need_context: Optional[bool] = None,
        only_need_prompt: Optional[bool] = None,
        top_k: Optional[int] = None,
        enable_rerank: Optional[bool] = True,
        max_results_per_dataset: Optional[int] = 20,
        **kwargs,
    ) -> CrossDatasetQueryResponse:
        """Execute a query across multiple datasets.
        
        Args:
            query: Query text.
            dataset_ids: List of dataset UUIDs to query (1-10 datasets).
            document_filters: Optional document ID filters per dataset.
            mode: Query mode.
            only_need_context: Return only retrieved context.
            only_need_prompt: Return only the generated prompt.
            top_k: Number of top results per dataset.
            enable_rerank: Enable cross-dataset reranking.
            max_results_per_dataset: Max results to retrieve per dataset.
            **kwargs: Additional query parameters.
            
        Returns:
            Cross-dataset query response with merged results.
        """
        request_data = {
            "query": query,
            "dataset_ids": dataset_ids,
            "mode": mode.value if isinstance(mode, QueryMode) else mode,
        }
        
        if document_filters is not None:
            request_data["document_filters"] = document_filters
        if only_need_context is not None:
            request_data["only_need_context"] = only_need_context
        if only_need_prompt is not None:
            request_data["only_need_prompt"] = only_need_prompt
        if top_k is not None:
            request_data["top_k"] = top_k
        if enable_rerank is not None:
            request_data["enable_rerank"] = enable_rerank
        if max_results_per_dataset is not None:
            request_data["max_results_per_dataset"] = max_results_per_dataset
        
        request_data.update(kwargs)
        
        response = await self._http.post(
            "/datasets/cross-query",
            json=request_data,
        )
        
        return CrossDatasetQueryResponse(**response)
    
    async def image_query(
        self,
        dataset_id: str,
        image: Union[str, bytes],
        query: Optional[str] = None,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> QueryResponse:
        """Execute an image-based RAG query.
        
        Args:
            dataset_id: Target dataset UUID.
            image: Image URL or base64-encoded image data.
            query: Optional text query to accompany the image.
            mode: Query mode.
            **kwargs: Additional query parameters.
            
        Returns:
            Query response with generated answer.
        """
        import base64
        
        request_data = {
            "mode": mode.value if isinstance(mode, QueryMode) else mode,
            **kwargs,
        }
        
        if query:
            request_data["query"] = query
        
        if isinstance(image, bytes):
            request_data["image_base64"] = base64.b64encode(image).decode("utf-8")
        elif image.startswith("http://") or image.startswith("https://"):
            request_data["image_url"] = image
        else:
            # Assume it's already base64 encoded
            request_data["image_base64"] = image
        
        response = await self._http.post(
            f"/datasets/{dataset_id}/query",
            json=request_data,
        )
        
        return QueryResponse(**response)
    
    async def get_context(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        top_k: Optional[int] = None,
        **kwargs,
    ) -> QueryResponse:
        """Get only the retrieved context without generating a response.
        
        Args:
            dataset_id: Target dataset UUID.
            query: Query text.
            mode: Query mode.
            top_k: Number of top results.
            **kwargs: Additional query parameters.
            
        Returns:
            Query response with entities, relationships, and chunks.
        """
        return await self.query(
            dataset_id=dataset_id,
            query=query,
            mode=mode,
            only_need_context=True,
            top_k=top_k,
            **kwargs,
        )
