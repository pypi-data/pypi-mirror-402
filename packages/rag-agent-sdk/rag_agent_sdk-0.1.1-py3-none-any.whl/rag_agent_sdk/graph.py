"""
RAG Agent SDK - Graph Client.

This module provides knowledge graph operations.
"""

from typing import Any, Dict, List, Optional

from .models import (
    KnowledgeGraph,
    Entity,
    Relation,
    EntityUpdateRequest,
    RelationUpdateRequest,
)


class GraphClient:
    """Client for knowledge graph operations.
    
    Provides methods for querying and editing the knowledge graph.
    """
    
    def __init__(self, http_client):
        """Initialize graph client.
        
        Args:
            http_client: HTTP client instance for making requests.
        """
        self._http = http_client
    
    async def get_knowledge_graph(
        self,
        dataset_id: str,
        label: str,
        max_depth: int = 3,
        max_nodes: int = 1000,
    ) -> KnowledgeGraph:
        """Get knowledge graph subgraph by label.
        
        Retrieves a connected subgraph of nodes where the label includes
        the specified label.
        
        Args:
            dataset_id: Dataset UUID.
            label: Label of the starting node.
            max_depth: Maximum depth of the subgraph (default: 3).
            max_nodes: Maximum nodes to return (default: 1000).
            
        Returns:
            Knowledge graph with nodes and edges.
        """
        params = {
            "label": label,
            "max_depth": max_depth,
            "max_nodes": max_nodes,
        }
        
        response = await self._http.get(
            f"/datasets/{dataset_id}/graphs",
            params=params,
        )
        
        return KnowledgeGraph(**response)
    
    async def get_labels(self, dataset_id: str) -> List[str]:
        """Get all graph labels in a dataset.
        
        Args:
            dataset_id: Dataset UUID.
            
        Returns:
            List of graph labels.
        """
        response = await self._http.get(
            f"/datasets/{dataset_id}/graph/label/list"
        )
        
        return response if isinstance(response, list) else response.get("labels", [])
    
    async def check_entity_exists(
        self,
        dataset_id: str,
        entity_name: str,
    ) -> bool:
        """Check if an entity exists in the knowledge graph.
        
        Args:
            dataset_id: Dataset UUID.
            entity_name: Name of the entity to check.
            
        Returns:
            True if entity exists, False otherwise.
        """
        response = await self._http.get(
            f"/datasets/{dataset_id}/graph/entity/exists",
            params={"name": entity_name},
        )
        
        return response.get("exists", False)
    
    async def get_entity(
        self,
        dataset_id: str,
        entity_name: str,
    ) -> Optional[Entity]:
        """Get entity by name.
        
        Args:
            dataset_id: Dataset UUID.
            entity_name: Name of the entity.
            
        Returns:
            Entity information or None if not found.
        """
        try:
            response = await self._http.get(
                f"/datasets/{dataset_id}/graph/entity",
                params={"name": entity_name},
            )
            return Entity(**response) if response else None
        except Exception:
            return None
    
    async def edit_entity(
        self,
        dataset_id: str,
        entity_name: str,
        updated_data: Dict[str, Any],
        allow_rename: bool = False,
    ) -> Dict[str, Any]:
        """Edit an entity in the knowledge graph.
        
        Args:
            dataset_id: Dataset UUID.
            entity_name: Name of the entity to edit.
            updated_data: Dictionary of properties to update.
            allow_rename: Allow renaming the entity (default: False).
            
        Returns:
            Update result with status and updated entity data.
        """
        request_data = {
            "entity_name": entity_name,
            "updated_data": updated_data,
            "allow_rename": allow_rename,
        }
        
        return await self._http.post(
            f"/datasets/{dataset_id}/graph/entity/edit",
            json=request_data,
        )
    
    async def edit_relation(
        self,
        dataset_id: str,
        source_id: str,
        target_id: str,
        updated_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Edit a relation in the knowledge graph.
        
        Args:
            dataset_id: Dataset UUID.
            source_id: Source entity ID.
            target_id: Target entity ID.
            updated_data: Dictionary of properties to update.
            
        Returns:
            Update result with status and updated relation data.
        """
        request_data = {
            "source_id": source_id,
            "target_id": target_id,
            "updated_data": updated_data,
        }
        
        return await self._http.post(
            f"/datasets/{dataset_id}/graph/relation/edit",
            json=request_data,
        )
    
    async def search_entities(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 10,
    ) -> List[Entity]:
        """Search for entities matching a query.
        
        Args:
            dataset_id: Dataset UUID.
            query: Search query.
            top_k: Number of top results.
            
        Returns:
            List of matching entities.
        """
        response = await self._http.get(
            f"/datasets/{dataset_id}/graph/entity/search",
            params={"query": query, "top_k": top_k},
        )
        
        entities = response if isinstance(response, list) else response.get("entities", [])
        return [Entity(**e) for e in entities]
    
    async def search_relations(
        self,
        dataset_id: str,
        query: str,
        top_k: int = 10,
    ) -> List[Relation]:
        """Search for relations matching a query.
        
        Args:
            dataset_id: Dataset UUID.
            query: Search query.
            top_k: Number of top results.
            
        Returns:
            List of matching relations.
        """
        response = await self._http.get(
            f"/datasets/{dataset_id}/graph/relation/search",
            params={"query": query, "top_k": top_k},
        )
        
        relations = response if isinstance(response, list) else response.get("relations", [])
        return [Relation(**r) for r in relations]
    
    async def get_entity_neighbors(
        self,
        dataset_id: str,
        entity_name: str,
        max_depth: int = 1,
    ) -> KnowledgeGraph:
        """Get neighboring entities of a given entity.
        
        Args:
            dataset_id: Dataset UUID.
            entity_name: Name of the center entity.
            max_depth: Maximum depth of neighbors to fetch.
            
        Returns:
            Knowledge graph with the entity and its neighbors.
        """
        return await self.get_knowledge_graph(
            dataset_id=dataset_id,
            label=entity_name,
            max_depth=max_depth,
        )
