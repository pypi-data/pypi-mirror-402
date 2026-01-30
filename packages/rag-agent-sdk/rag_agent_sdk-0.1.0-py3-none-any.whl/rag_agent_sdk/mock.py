"""
RAG Agent SDK Mock Client.

This module provides a mock client for testing without a real server.
Useful for unit tests and development.
"""

from typing import Any, AsyncIterator, Dict, List, Optional, Union
from datetime import datetime
import uuid

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


class MockDatasetsClient:
    """Mock datasets client for testing."""
    
    def __init__(self):
        self._datasets: Dict[str, Dataset] = {}
    
    async def create(
        self,
        name: str,
        description: Optional[str] = None,
        storage_type: str = "local",
        chunk_engine: str = "token",
        **kwargs,
    ) -> Dataset:
        dataset_id = str(uuid.uuid4())
        dataset = Dataset(
            dataset_uuid=dataset_id,
            name=name,
            description=description,
            rag_type="rag",
            storage_type=storage_type,
            chunk_engine=chunk_engine,
            status="active",
            visibility="private",
            default_permission="none",
            args={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._datasets[dataset_id] = dataset
        return dataset
    
    async def get(self, dataset_id: str) -> Dataset:
        if dataset_id not in self._datasets:
            from .exceptions import DatasetNotFoundError
            raise DatasetNotFoundError(dataset_id)
        return self._datasets[dataset_id]
    
    async def get_by_name(self, name: str) -> Optional[Dataset]:
        for dataset in self._datasets.values():
            if dataset.name == name:
                return dataset
        return None
    
    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ) -> DatasetListResponse:
        datasets = list(self._datasets.values())
        start = (page - 1) * page_size
        end = start + page_size
        return DatasetListResponse(
            datasets=datasets[start:end],
            total=len(datasets),
            page=page,
            page_size=page_size,
        )
    
    async def update(self, dataset_id: str, **updates) -> Dataset:
        dataset = await self.get(dataset_id)
        for key, value in updates.items():
            if hasattr(dataset, key) and value is not None:
                setattr(dataset, key, value)
        return dataset
    
    async def delete(self, dataset_id: str) -> Dict[str, str]:
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
        return {"status": "deleted", "message": f"Dataset {dataset_id} deleted"}


class MockDocumentsClient:
    """Mock documents client for testing."""
    
    def __init__(self):
        self._documents: Dict[str, Dict[str, Document]] = {}
    
    async def upload(
        self,
        dataset_id: str,
        file: Any,
        filename: Optional[str] = None,
    ) -> InsertResponse:
        return await self._insert(dataset_id, f"Uploaded: {filename or 'file'}")
    
    async def insert_text(
        self,
        dataset_id: str,
        text: str,
        source: Optional[str] = None,
    ) -> InsertResponse:
        return await self._insert(dataset_id, text, source)
    
    async def _insert(
        self,
        dataset_id: str,
        content: str,
        source: Optional[str] = None,
    ) -> InsertResponse:
        doc_id = str(uuid.uuid4())
        track_id = f"track-{uuid.uuid4().hex[:8]}"
        
        if dataset_id not in self._documents:
            self._documents[dataset_id] = {}
        
        self._documents[dataset_id][doc_id] = Document(
            id=doc_id,
            content_summary=content[:100],
            content_length=len(content),
            status=DocStatus.PROCESSED,
            file_path=source,
            created_at=datetime.utcnow(),
        )
        
        return InsertResponse(
            status="success",
            message="Document inserted",
            track_id=track_id,
            doc_id=doc_id,
        )
    
    async def insert_batch(
        self,
        dataset_id: str,
        texts: List[str],
        sources: Optional[List[str]] = None,
    ) -> InsertResponse:
        for i, text in enumerate(texts):
            source = sources[i] if sources and i < len(sources) else None
            await self._insert(dataset_id, text, source)
        
        return InsertResponse(
            status="success",
            message=f"Inserted {len(texts)} documents",
            track_id=f"batch-{uuid.uuid4().hex[:8]}",
        )
    
    async def list(
        self,
        dataset_id: str,
        status: Optional[DocStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> DocumentListResponse:
        docs = list(self._documents.get(dataset_id, {}).values())
        if status:
            docs = [d for d in docs if d.status == status]
        
        start = (page - 1) * page_size
        end = start + page_size
        return DocumentListResponse(
            documents=docs[start:end],
            total=len(docs),
            page=page,
            page_size=page_size,
        )
    
    async def get(self, dataset_id: str, doc_id: str) -> Document:
        docs = self._documents.get(dataset_id, {})
        if doc_id not in docs:
            from .exceptions import DocumentNotFoundError
            raise DocumentNotFoundError(doc_id, dataset_id)
        return docs[doc_id]
    
    async def get_status(self, dataset_id: str, doc_id: str) -> Document:
        return await self.get(dataset_id, doc_id)
    
    async def delete(self, dataset_id: str, doc_id: str) -> Dict[str, Any]:
        if dataset_id in self._documents and doc_id in self._documents[dataset_id]:
            del self._documents[dataset_id][doc_id]
        return {"status": "deleted"}
    
    async def scan(self, dataset_id: str) -> ScanResponse:
        return ScanResponse(
            status="success",
            message="Scan completed",
            track_id=f"scan-{uuid.uuid4().hex[:8]}",
        )
    
    async def clear(self, dataset_id: str) -> Dict[str, str]:
        if dataset_id in self._documents:
            self._documents[dataset_id] = {}
        return {"status": "cleared"}


class MockQueryClient:
    """Mock query client for testing."""
    
    def __init__(self, default_response: str = "This is a mock response from RAG Agent SDK."):
        self.default_response = default_response
        self.responses: Dict[str, str] = {}
    
    def set_response(self, query: str, response: str) -> None:
        """Set a custom response for a specific query."""
        self.responses[query] = response
    
    async def query(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> QueryResponse:
        response = self.responses.get(query, self.default_response)
        return QueryResponse(
            response=response,
            dataset_id=dataset_id,
            query_mode=mode if isinstance(mode, str) else mode.value,
            entities=[
                Entity(name="MockEntity", type="test", description="A mock entity", properties={}),
            ],
            chunks=[],
        )
    
    async def query_stream(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> AsyncIterator[str]:
        response = self.responses.get(query, self.default_response)
        # Simulate streaming by yielding word by word
        for word in response.split():
            yield word + " "
    
    async def cross_dataset_query(
        self,
        query: str,
        dataset_ids: List[str],
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> CrossDatasetQueryResponse:
        response = self.responses.get(query, self.default_response)
        return CrossDatasetQueryResponse(
            response=response,
            query=query,
            dataset_count=len(dataset_ids),
            total_chunks=0,
            query_mode=mode if isinstance(mode, str) else mode.value,
            dataset_results={},
        )
    
    async def get_context(
        self,
        dataset_id: str,
        query: str,
        mode: Union[str, QueryMode] = "mix",
        **kwargs,
    ) -> QueryResponse:
        return QueryResponse(
            response="",
            dataset_id=dataset_id,
            query_mode=mode if isinstance(mode, str) else mode.value,
            entities=[
                Entity(name="MockEntity1", type="concept", description="Mock entity 1", properties={}),
                Entity(name="MockEntity2", type="concept", description="Mock entity 2", properties={}),
            ],
            relationships=[
                Relation(source="MockEntity1", target="MockEntity2", type="related_to", properties={}),
            ],
            chunks=[],
        )


class MockGraphClient:
    """Mock graph client for testing."""
    
    async def get_knowledge_graph(
        self,
        dataset_id: str,
        label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ) -> KnowledgeGraph:
        return KnowledgeGraph(
            nodes=[
                {"id": "1", "label": label, "properties": {}},
                {"id": "2", "label": "RelatedNode", "properties": {}},
            ],
            edges=[
                {"source": "1", "target": "2", "type": "connected_to"},
            ],
        )
    
    async def get_labels(self, dataset_id: str) -> List[str]:
        return ["MockLabel1", "MockLabel2", "MockLabel3"]
    
    async def check_entity_exists(self, dataset_id: str, entity_name: str) -> bool:
        return True
    
    async def get_entity(self, dataset_id: str, entity_name: str) -> Optional[Entity]:
        return Entity(
            name=entity_name,
            type="mock",
            description=f"Mock entity: {entity_name}",
            properties={},
        )
    
    async def edit_entity(
        self,
        dataset_id: str,
        entity_name: str,
        updated_data: Dict[str, Any],
        allow_rename: bool = False,
    ) -> Dict[str, Any]:
        return {"status": "updated", "entity_name": entity_name}
    
    async def search_entities(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 10,
    ) -> List[Entity]:
        return [
            Entity(name=f"Result{i}", type="mock", description=f"Search result {i}", properties={})
            for i in range(min(top_k, 3))
        ]


class MockRagAgentClient:
    """Mock client for testing without a real server.
    
    This client simulates RAG Agent API responses without making
    actual network requests. Useful for unit tests.
    
    Example:
        ```python
        from rag_agent_sdk.mock import MockRagAgentClient
        
        # Use mock client in tests
        client = MockRagAgentClient()
        
        # Set custom responses
        client.query.set_response(
            "What is RAG?",
            "RAG stands for Retrieval-Augmented Generation..."
        )
        
        # Use like normal client
        dataset = await client.datasets.create(name="test-kb")
        response = await client.query.query(dataset.dataset_uuid, "What is RAG?")
        assert "Retrieval-Augmented" in response.response
        ```
    """
    
    def __init__(self, default_response: str = "This is a mock response."):
        """Initialize mock client.
        
        Args:
            default_response: Default response for queries.
        """
        self.datasets = MockDatasetsClient()
        self.documents = MockDocumentsClient()
        self.query = MockQueryClient(default_response)
        self.graph = MockGraphClient()
        self._base_url = "http://mock-server:9621"
    
    @property
    def base_url(self) -> str:
        return self._base_url
    
    @property
    def is_authenticated(self) -> bool:
        return True
    
    async def health_check(self) -> dict:
        return {"status": "healthy", "mock": True}
    
    async def close(self) -> None:
        pass
    
    async def __aenter__(self) -> "MockRagAgentClient":
        return self
    
    async def __aexit__(self, *args) -> None:
        pass
