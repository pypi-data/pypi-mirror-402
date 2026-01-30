from dataclasses import dataclass
from typing import Dict, List

from neo4j import AsyncDriver


@dataclass
class Entity:
    id: str
    type: str
    properties: Dict[str, any]


@dataclass
class CreateEntityRequest:
    type: str
    properties: Dict[str, any]


@dataclass
class CreateEntitiesResult:
    result: List[Entity]


async def create_entities(driver: AsyncDriver, entities: List[CreateEntityRequest]) -> CreateEntitiesResult:
    """Create multiple new entities in the knowledge graph
    
    Args:
        driver: Neo4j async driver instance
        entities: List of entity requests with type and properties fields
        
    Returns:
        CreateEntitiesResult containing the created entities with their properties
    """
    results = []

    async with driver.session() as session:
        for entity in entities:
            # Create node with entity type as label and all properties
            query = """
            CREATE (n:Entity)
            SET n = $properties
            SET n.type = $type
            WITH n, $type as type
            CALL apoc.create.addLabels(n, [type]) YIELD node
            RETURN {
                id: node.id,
                type: node.type,
                properties: properties(node)
            } as result
            """
            
            # Ensure id is set (use name if not provided)
            properties = dict(entity.properties)
            if "id" not in properties:
                properties["id"] = properties.get("name")
            
            params = {
                "properties": properties,
                "type": entity.type
            }

            result = await session.run(query, params)
            record = await result.single()
            if record:
                node_data = record["result"]
                results.append(Entity(
                    id=node_data["id"],
                    type=node_data["type"],
                    properties=node_data["properties"]
                ))

    return CreateEntitiesResult(result=results)
