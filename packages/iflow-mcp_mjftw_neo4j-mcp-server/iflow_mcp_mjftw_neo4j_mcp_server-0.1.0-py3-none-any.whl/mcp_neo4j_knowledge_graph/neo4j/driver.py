import os
from neo4j import AsyncDriver, AsyncGraphDatabase


async def create_neo4j_driver(
    uri: str = "neo4j://localhost:7687",
    username: str = "neo4j",
    password: str = "password"
) -> AsyncDriver:
    """Create an async Neo4j driver with the given configuration.

    Args:
        uri: Neo4j connection URI (default: bolt://localhost:7687)
        username: Neo4j username (default: neo4j)
        password: Neo4j password (default: password)

    Returns:
        AsyncDriver: Configured Neo4j driver instance

    Raises:
        Exception: If connection verification fails
    """
    # Check if running in test/demo mode without database
    if os.getenv("NEO4J_DEMO_MODE") == "true":
        # Return a mock driver for demo purposes
        return MockDriver()

    driver = AsyncGraphDatabase.driver(
        uri,
        auth=(username, password)
    )

    # Verify connectivity before returning
    await driver.verify_connectivity()
    return driver


class MockDriver:
    """Mock driver for demo/testing without Neo4j database."""

    async def verify_connectivity(self):
        """Mock connectivity verification."""
        return True

    async def close(self):
        """Mock close."""
        pass

    async def execute_query(self, query, parameters=None, **kwargs):
        """Mock query execution."""
        return MockResult()

    def session(self):
        """Mock session."""
        return MockSession()


class MockResult:
    """Mock result."""

    def __init__(self):
        self.records = []

    async def consume(self):
        """Mock consume."""
        return self.records


class MockSession:
    """Mock session."""

    async def run(self, query, parameters=None, **kwargs):
        """Mock run."""
        return MockResult()

    async def close(self):
        """Mock close."""
        pass