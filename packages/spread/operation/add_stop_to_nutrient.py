from neo4j import GraphDatabase
from pydantic import BaseModel

from spread.operation.framework import Operation

class EngagementData(BaseModel):
    nutrient_id: str

class AddStopToNutrient(Operation):
    def __init__(self, graph, engagement_handle, max_relevant_claims: int = 3):
        super().__init__(graph, engagement_handle, operation_name="add_stop_to_nutrient")
        self.max_relevant_claims = max_relevant_claims

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_nutrient_without_stop_node(self.graph, self.operation_name, self.max_relevant_claims)
        if self.engagement_data is not None:
            return self.engagement_data.nutrient_id
        else:
            return None

    async def act_on_engaged_node(self):
        create_stop(self.graph, self.engagement_data.nutrient_id)


def query_nutrient_without_stop_node(graph: GraphDatabase.driver, operation_name: str, max_relevant_claims: int):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE NOT (nutrient)-[:STOPPED_BY]->(:Stop)
            AND count{(claim:Claim)-[:RELEVANT_TO]->(nutrient)} >= $max_relevant_claims
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(nutrient)
        RETURN elementId(nutrient)
        """,
        operation_name=operation_name,
        max_relevant_claims=max_relevant_claims)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(nutrient_id=record[0])
    return engagement_data

def create_stop(graph, nutrient_id):
    graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE elementId(nutrient) = $nutrient_id
        CREATE (stop:Stop {nutrient_id: elementId(nutrient)})<-[:STOPPED_BY]-(nutrient)
        """,
        nutrient_id=nutrient_id)