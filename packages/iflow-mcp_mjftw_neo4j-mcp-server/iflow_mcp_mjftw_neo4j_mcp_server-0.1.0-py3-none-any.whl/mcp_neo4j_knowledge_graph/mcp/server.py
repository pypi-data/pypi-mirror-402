from contextlib import asynccontextmanager

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Import tool registration functions
from mcp_neo4j_knowledge_graph.mcp.tools import create_entities
from mcp_neo4j_knowledge_graph.mcp.tools import create_relations
from mcp_neo4j_knowledge_graph.mcp.tools import delete_entities
from mcp_neo4j_knowledge_graph.mcp.tools import introspect_schema
from mcp_neo4j_knowledge_graph.mcp.tools import search_entities
from mcp_neo4j_knowledge_graph.mcp.tools import update_entities
from mcp_neo4j_knowledge_graph.neo4j.driver import create_neo4j_driver

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(mcp: FastMCP):
    # Initialize Neo4j driver with docker-compose configuration
    driver = await create_neo4j_driver()

    try:
        # Verify connection
        await driver.verify_connectivity()

        # Register all tools
        await create_entities.register_tools(mcp, driver)
        await create_relations.register_tools(mcp, driver)
        await delete_entities.register_tools(mcp, driver)
        await introspect_schema.register_tools(mcp, driver)
        await search_entities.register_tools(mcp, driver)
        await update_entities.register_tools(mcp, driver)

        # Initialize state dictionary
        mcp.state = {"driver": driver}
        print("Successfully connected to Neo4j")
        yield {"driver": driver}
    finally:
        # Close the driver when the server shuts down
        await driver.close()


def create_server():
    return FastMCP(lifespan=lifespan)


def main():
    print("Starting Neo4j MCP server with stdio transport")
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()