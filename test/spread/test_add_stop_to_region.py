import pytest
from neo4j import GraphDatabase

from communal.graph import clear_graph
from test.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count

@pytest.mark.asyncio
async def test_no_work_to_do():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        add_stop_to_region_operation = AddStopToRegion(graph, "test")
        assert await add_stop_to_region_operation.operate() is False
        assert query_node_count(graph) == 0