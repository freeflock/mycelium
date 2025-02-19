import pytest
from neo4j import AsyncGraphDatabase

from communal.graph import create_nutrient, clear_graph
from spread.operation.spore import spore
from test.spread.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count


@pytest.mark.asyncio
async def test_no_work_to_do():
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        await clear_graph(graph)
        assert await spore(graph, "test") is False
        assert await query_node_count(graph) == 0


@pytest.mark.asyncio
async def test_success():
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        await clear_graph(graph)
        await create_nutrient(graph, "mycelium", "test", "mycelium in a fungal context")
        assert await spore(graph, "test") is True
        assert await query_node_count(graph) == 3
