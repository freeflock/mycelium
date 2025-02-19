import pytest
from neo4j import AsyncGraphDatabase

from communal.graph import clear_graph, create_nutrient
from spread.operation.add_region_to_spore import add_region_to_spore
from spread.operation.collect_finding import collect_finding
from spread.operation.isolate_claims import isolate_claims
from spread.operation.spore import spore
from test.spread.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count


@pytest.mark.asyncio
async def test_no_work_to_do():
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        await clear_graph(graph)
        assert await isolate_claims(graph, "test") is False
        assert await query_node_count(graph) == 0


@pytest.mark.asyncio
async def test_success():
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        await clear_graph(graph)
        await create_nutrient(graph, "mycelium", "test", "mycelium in a fungal context")
        assert await spore(graph, "test") is True
        assert await add_region_to_spore(graph, "test") is True
        assert await collect_finding(graph, "test") is True
        pre_claim_count = await query_node_count(graph)
        assert await isolate_claims(graph, "test") is True
        assert await query_node_count(graph) > pre_claim_count
