import pytest
from neo4j import GraphDatabase

from communal.graph import clear_graph, create_nutrient
from spread.operation.add_region_to_spore import AddRegionToSpore
from spread.operation.collect_finding import CollectFinding
from spread.operation.isolate_claims import IsolateClaims
from spread.operation.spore import Spore
from test.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count


@pytest.mark.asyncio
async def test_no_work_to_do():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        isolate_claims_operation = IsolateClaims(graph, "test")
        assert await isolate_claims_operation.operate() is False
        assert query_node_count(graph) == 0


@pytest.mark.asyncio
async def test_success():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        create_nutrient(graph, "mycelium", "test", "mycelium in a fungal context")
        spore_operation = Spore(graph, "test")
        assert await spore_operation.operate() is True

        add_region_to_spore_operation = AddRegionToSpore(graph, "test")
        assert await add_region_to_spore_operation.operate() is True

        collect_finding_operation = CollectFinding(graph, "test")
        assert await collect_finding_operation.operate() is True

        pre_claim_count = query_node_count(graph)
        isolate_claims_operation = IsolateClaims(graph, "test")
        assert await isolate_claims_operation.operate() is True
        assert query_node_count(graph) > pre_claim_count
