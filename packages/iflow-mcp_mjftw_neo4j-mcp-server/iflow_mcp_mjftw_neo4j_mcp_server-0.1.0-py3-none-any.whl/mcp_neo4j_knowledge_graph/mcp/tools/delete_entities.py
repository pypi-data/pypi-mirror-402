from typing import Dict, List

from neo4j import AsyncDriver
from mcp.server.fastmcp import FastMCP

from mcp_neo4j_knowledge_graph.neo4j.operations.delete_entities import delete_entities as delete_entities_impl, DeleteEntityRequest


async def register_tools(server: FastMCP, driver: AsyncDriver) -> None:
    """Register the delete_entities tool with the MCP server."""
    
    @server.tool("delete_entities")
    async def delete_entities(
        entity_ids: List[str],
        cascade: bool = False,
        dry_run: bool = False,
        context: Dict = None
    ) -> Dict:
        """Delete entities from the knowledge graph with relationship handling and impact analysis.
        
        Provides safe deletion of entities with options for:
        - Cascading deletion of relationships
        - Dry run impact analysis
        - Prevention of orphaned relationships
        
        The operation can be previewed using dry_run to see what would be affected
        without making any changes. When cascade is False, the operation will fail
        if there are any relationships that would become orphaned.
        
        Args:
            entity_ids: List[String] - IDs of entities to delete
            cascade: Boolean - If True, also delete all relationships connected to
                    these entities. If False, fail if any relationships exist
                    (default: False)
            dry_run: Boolean - If True, only analyze and return what would be
                    deleted without making changes (default: False)
            context: Optional[Dict] - Additional context for the deletion operation
            
        Returns:
            Dict containing:
                - success: Boolean - Whether the operation was successful
                - deleted_entities: List[Dict] - Entities that were deleted, each with:
                    - id: String - Entity's identifier
                    - type: List[String] - Entity's labels
                    - properties: Dict - Entity's properties
                - deleted_relationships: List[Dict] - Relationships that were deleted
                  (when cascade=True), each with:
                    - type: String - Relationship type
                    - from: String - Source entity ID
                    - to: String - Target entity ID
                    - properties: Dict - Relationship properties
                - errors: Optional[List[String]] - Error messages if operation failed
                - impacted_entities: Optional[List[Dict]] - When dry_run=True, entities
                  that would be deleted
                - impacted_relationships: Optional[List[Dict]] - When dry_run=True,
                  relationships that would be deleted
                
        Raises:
            ValueError: If entities don't exist or would create orphaned relationships
            Neo4jError: For database-level errors
            
        Notes:
            - All specified entities must exist
            - Without cascade=True, all entities must have no relationships
            - With cascade=True, all connected relationships will be deleted
            - dry_run=True allows safely checking the impact before deletion
            - The operation is atomic - either all specified entities are deleted
              or none are
        """
        requests = [DeleteEntityRequest(id=id, cascade=cascade) for id in entity_ids]
        result = await delete_entities_impl(driver, requests, dry_run)
        return result.__dict__ 