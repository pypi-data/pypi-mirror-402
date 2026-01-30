from typing import Any, Dict, List, Optional
from neo4j import AsyncDriver
from mcp.server.fastmcp import FastMCP

from mcp_neo4j_knowledge_graph.neo4j.operations.search_entities import search_entities as search_entities_impl, SearchEntityRequest, Entity, SearchEntitiesResult


async def register_tools(server: FastMCP, driver: AsyncDriver) -> None:
    """Register the search_entities tool with the MCP server."""
    
    @server.tool("search_entities")
    async def search_entities(
        search_term: Optional[str] = None,
        entity_type: Optional[str] = None,
        properties: Optional[List[str]] = None,
        include_relationships: bool = False,
        fuzzy_match: bool = True
    ) -> Dict[str, Any]:
        """Search for entities in the knowledge graph with powerful text matching and filtering.
        
        Performs a flexible search across entities with options for:
        - Fuzzy text matching (case-insensitive partial matches)
        - Filtering by entity type
        - Filtering by property existence
        - Including related entities and relationships
        
        Args:
            search_term: Optional[String] - The text to search for in entity properties.
                        If not provided, returns entities based on other filters.
            entity_type: Optional[String] - Filter results to entities of this type.
                        If provided alone, returns all entities of that type.
            properties: Optional[List[String]] - List of property names to filter by.
                       If search_term is provided, searches these properties for the term.
                       If search_term is not provided, returns entities that have any
                       of these properties defined.
            include_relationships: Boolean - Whether to include connected entities and
                                 relationships in the results (default: False)
            fuzzy_match: Boolean - Whether to use case-insensitive partial matching
                        when search_term is provided (default: True)
            
        Returns:
            Dict containing:
                results: List of matching entities, each with:
                    - id: String - Entity's unique identifier
                    - type: List[String] - Entity's type labels
                    - properties: Dict - All properties of the entity
                    - relationships: Optional[List[Dict]] - If include_relationships is True,
                      list of related entities with:
                        - type: String - Relationship type
                        - direction: String - 'incoming' or 'outgoing'
                        - node: Dict - Connected entity's data (id, type, properties)
                    
        Notes:
            - Can be used to:
              1. Search by text across all or specific properties
              2. List all entities of a specific type
              3. Find entities with specific properties defined
              4. Any combination of the above
            - When no filters are provided, returns all entities
            - When fuzzy_match is True, search terms use case-insensitive partial matching
            - Entity type filtering is exact match (not fuzzy)
        """
        
        search_request = SearchEntityRequest(
            search_term=search_term,
            entity_type=entity_type,
            properties=properties,
            include_relationships=include_relationships,
            fuzzy_match=fuzzy_match
        )
        
        result = await search_entities_impl(driver, search_request)
        
        # Convert result back to dict format for MCP interface
        return {
            "results": [
                {
                    "id": entity.id,
                    "type": entity.type,
                    "properties": entity.properties,
                    **({"relationships": entity.relationships} if entity.relationships else {})
                } for entity in result.results
            ]
        } 