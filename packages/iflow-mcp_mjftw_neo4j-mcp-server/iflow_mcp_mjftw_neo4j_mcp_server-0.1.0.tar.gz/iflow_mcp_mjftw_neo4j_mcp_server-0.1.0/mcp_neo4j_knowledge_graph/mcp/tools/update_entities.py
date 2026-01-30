from typing import Dict, List

from neo4j import AsyncDriver
from mcp.server.fastmcp import FastMCP

from mcp_neo4j_knowledge_graph.neo4j.operations.update_entities import update_entities as update_entities_impl, UpdateEntityRequest


async def register_tools(server: FastMCP, driver: AsyncDriver) -> None:
    """Register the update_entities tool with the MCP server."""
    
    @server.tool("update_entities")
    async def update_entities(
        updates: List[Dict],
        context: Dict = None
    ) -> Dict:
        """Update existing entities in the knowledge graph with comprehensive modification options.
        
        Provides atomic updates to entities including:
        - Adding or updating properties
        - Removing specific properties
        - Adding new labels/types
        - Removing existing labels/types
        
        All updates in a request are processed as a batch, but each entity update
        is independent. If one update fails, others will still proceed.
        
        Args:
            updates: List of update requests, each containing:
                - id: String (required) - ID of the entity to update
                - properties: Optional[Dict] - Properties to add or update
                - remove_properties: Optional[List[String]] - Property names to remove
                - add_labels: Optional[List[String]] - Labels to add to the entity
                - remove_labels: Optional[List[String]] - Labels to remove from the entity
            context: Optional[Dict] - Additional context for the update operation
            
        Returns:
            Dict containing:
                - success: Boolean - True if all updates succeeded, False if any failed
                - updated_entities: List[Dict] - Entities after updates, each with:
                    - id: String - Entity's identifier
                    - type: List[String] - Entity's current labels
                    - properties: Dict - All current properties
                - errors: Optional[List[String]] - Error messages if any updates failed
                
        Raises:
            ValueError: If entity IDs don't exist or update format is invalid
            Neo4jError: For database-level errors
            
        Notes:
            - At least one modification (properties, remove_properties, add_labels,
              or remove_labels) must be specified
            - Property updates are merged with existing properties
            - Removing a non-existent property or label is not an error
            - The Entity label and type cannot be removed
            - Updates are atomic per entity
        """
        requests = [UpdateEntityRequest(**update) for update in updates]
        result = await update_entities_impl(driver, requests)
        return result.__dict__ 