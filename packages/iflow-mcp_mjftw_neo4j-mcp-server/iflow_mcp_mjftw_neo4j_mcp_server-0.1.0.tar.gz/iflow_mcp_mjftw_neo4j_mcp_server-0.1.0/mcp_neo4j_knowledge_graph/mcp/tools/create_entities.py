from typing import Dict, List

from neo4j import AsyncDriver
from mcp.server.fastmcp import FastMCP

from mcp_neo4j_knowledge_graph.neo4j.operations.create_entities import create_entities as create_entities_impl, CreateEntityRequest

async def register_tools(server: FastMCP, driver: AsyncDriver) -> None:
    """Register the create_entities tool with the MCP server."""
    
    @server.tool("create_entities")
    async def create_entities(entities: List[Dict]) -> Dict:
        """Create multiple new entities in the knowledge graph.
        
        Each entity is created with:
        - An Entity label and the specified type as an additional label
        - All provided properties
        - An ID field (either provided or derived from the name property)
        
        Args:
            entities: List of entity dictionaries, each containing:
                - type: String - The type of entity (e.g., Person, Organization)
                - properties: Dict - Properties of the entity, must include either:
                    - id: String - Unique identifier for the entity
                    - name: String - Name used as ID if no ID provided
                    - Any additional properties as key-value pairs
            
        Returns:
            Dict containing:
                result: List of created entities, each with:
                    - id: String - Entity's unique identifier
                    - type: String - Entity's type label
                    - properties: Dict - All properties of the created entity
                    
        Raises:
            ValueError: If required fields are missing or invalid
            Neo4jError: If there are database errors (e.g., duplicate IDs)
        """
     
            
        # Convert input dicts to CreateEntityRequest objects
        entity_requests = [
            CreateEntityRequest(
                type=e["type"],
                properties=e["properties"]
            ) for e in entities
        ]
        
        result = await create_entities_impl(driver, entity_requests)
        
        # Convert result back to dict format for MCP interface
        return {
            "result": [
                {
                    "id": e.id,
                    "type": e.type,
                    "properties": e.properties
                } for e in result.result
            ]
        } 