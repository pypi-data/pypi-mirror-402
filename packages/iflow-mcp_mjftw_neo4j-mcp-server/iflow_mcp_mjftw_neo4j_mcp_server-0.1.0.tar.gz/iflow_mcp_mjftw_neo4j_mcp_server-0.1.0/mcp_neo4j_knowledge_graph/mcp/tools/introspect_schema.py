from typing import Dict

from neo4j import AsyncDriver
from mcp.server.fastmcp import FastMCP

from mcp_neo4j_knowledge_graph.neo4j.operations.introspect_schema import introspect_schema as introspect_schema_impl


async def register_tools(server: FastMCP, driver: AsyncDriver) -> None:
    """Register the introspect_schema tool with the MCP server."""
    
    @server.tool("introspect_schema")
    async def introspect_schema(random_string: str) -> Dict:
        """Analyze and return the complete Neo4j database schema structure.
        
        Performs a comprehensive analysis of the database schema, including:
        - All node labels/types in use
        - All relationship types
        - Properties used for each node label
        - Properties used for each relationship type
        
        This tool is useful for:
        - Understanding the current database structure
        - Finding available entity types and their properties
        - Discovering relationship types between entities
        - Schema validation and consistency checking
        
        Args:
            random_string: String - Ignored parameter (required by MCP protocol)
            
        Returns:
            Dict containing:
                schema: Dict with:
                    - node_labels: List[String] - All node labels in the database
                    - relationship_types: List[String] - All relationship types
                    - node_properties: Dict[String, List[String]] - Map of node label
                      to list of property names used by nodes with that label
                    - relationship_properties: Dict[String, List[String]] - Map of
                      relationship type to list of property names used by those relationships
                
        Notes:
            - Includes only actually used labels and properties (not schema definitions)
            - Node labels include both Entity and specific type labels
            - Property lists include all properties found on any instance of that
              label/type (not all instances will have all properties)
            - Empty labels/types (with no instances) are not included
            - System properties (starting with '_') are excluded
        """
        if "driver" not in server.state:
            raise ValueError("Neo4j driver not found in server state")

        result = await introspect_schema_impl(driver)
        
        # Convert result back to dict format for MCP interface
        return {
            "schema": {
                "node_labels": result.node_labels,
                "relationship_types": result.relationship_types,
                "node_properties": result.node_properties,
                "relationship_properties": result.relationship_properties
            }
        } 