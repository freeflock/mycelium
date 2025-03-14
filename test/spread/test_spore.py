import pytest
from neo4j import GraphDatabase

from communal.graph import create_nutrient
from spread.operation.spore import Spore
from test.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count, clear_graph


@pytest.mark.asyncio
async def test_no_work_to_do():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        spore_operation = Spore(graph, "test")
        assert await spore_operation.operate() is False
        assert query_node_count(graph) == 0


@pytest.mark.asyncio
async def test_success():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        create_nutrient(graph, "mycelium", "test", "mycelium in a fungal context")
        spore_operation = Spore(graph, "test")
        assert await spore_operation.operate() is True
        assert query_node_count(graph) == 3
