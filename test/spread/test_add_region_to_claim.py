import pytest
from neo4j import GraphDatabase

from communal.graph import clear_graph, create_nutrient
from spread.operation.add_region_to_claim import add_region_to_claim
from spread.operation.add_region_to_spore import add_region_to_spore
from spread.operation.collect_finding import collect_finding
from spread.operation.determine_claim_relevance import determine_claim_relevance
from spread.operation.isolate_claims import isolate_claims
from spread.operation.spore import spore
from test.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count


@pytest.mark.asyncio
async def test_no_work_to_do():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        assert await add_region_to_claim(graph, "test") is False
        assert query_node_count(graph) == 0


@pytest.mark.asyncio
async def test_success():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        create_nutrient(graph, "mycelium", "test", "mycelium in a fungal context")
        assert await spore(graph, "test") is True
        assert await add_region_to_spore(graph, "test") is True
        assert await collect_finding(graph, "test") is True
        assert await isolate_claims(graph, "test") is True
        assert await determine_claim_relevance(graph, "test") is True
        pre_add_region_node_count = query_node_count(graph)
        assert await add_region_to_claim(graph, "test") is True
        assert query_node_count(graph) == pre_add_region_node_count + 2
