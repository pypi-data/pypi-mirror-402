from dataclasses import dataclass
from typing import List

from neo4j import AsyncDriver


@dataclass
class Relation:
    type: str
    from_id: str
    to_id: str


@dataclass
class CreateRelationRequest:
    type: str
    from_id: str
    to_id: str


@dataclass
class CreateRelationsResult:
    result: List[Relation]


async def create_relations(driver: AsyncDriver, relations: List[CreateRelationRequest]) -> CreateRelationsResult:
    """Create multiple new relations between entities in the knowledge graph
    
    Args:
        driver: Neo4j async driver instance
        relations: List of relation requests with from_id, to_id, and type fields
        
    Returns:
        CreateRelationsResult containing the created relations
    """
    results = []

    async with driver.session() as session:
        for relation in relations:
            # We need to use string formatting for the relationship type
            # as Neo4j doesn't support parameterized relationship types
            query = f"""
            MATCH (a:Entity {{id: $from_id}}), (b:Entity {{id: $to_id}})
            CREATE (a)-[r:{relation.type}]->(b)
            RETURN type(r) as type, a.id as from_id, b.id as to_id
            """
            params = {
                "from_id": relation.from_id,
                "to_id": relation.to_id
            }

            try:
                result = await session.run(query, params)
                record = await result.single()
                if record:
                    results.append(Relation(
                        type=record["type"],
                        from_id=record["from_id"],
                        to_id=record["to_id"]
                    ))
            except Exception:
                # If the query fails (e.g., entities not found), continue to next relation
                continue

    return CreateRelationsResult(result=results)
