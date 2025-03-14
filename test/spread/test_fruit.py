import pytest
from neo4j import GraphDatabase

from communal.graph import create_nutrient
from spread.operation.add_region_to_spore import AddRegionToSpore
from spread.operation.add_stop_to_nutrient import AddStopToNutrient
from spread.operation.collect_finding import CollectFinding
from spread.operation.determine_claim_relevance import DetermineClaimRelevance
from spread.operation.fruit import Fruit
from spread.operation.isolate_claims import IsolateClaims
from spread.operation.spore import Spore
from test.testkit import NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD, query_node_count, clear_graph


@pytest.mark.asyncio
async def test_no_work_to_do():
    # halt all spread containers before running this test
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        clear_graph(graph)
        fruit_operation = Fruit(graph, "test")
        assert await fruit_operation.operate() is False
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

        isolate_claims_operation = IsolateClaims(graph, "test")
        assert await isolate_claims_operation.operate() is True

        determine_claim_relevance_operation = DetermineClaimRelevance(graph, "test")
        assert await determine_claim_relevance_operation.operate() is True

        add_stop_to_nutrient_operation = AddStopToNutrient(graph, engagement_handle="test", max_relevant_claims=1)
        assert await add_stop_to_nutrient_operation.operate() is True

        fruit_operation = Fruit(graph, "test")
        assert await fruit_operation.operate() is True
