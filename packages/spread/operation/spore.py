from freeflock_contraptions.framework import Operation
from pydantic import BaseModel

from communal.graph import create_spore


class EngagementData(BaseModel):
    nutrient_id: str


class Spore(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "spore")

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_nutrient_without_seeking_spore(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.nutrient_id
        else:
            return None

    async def act_on_engaged_node(self):
        create_spore(self.graph, self.engagement_data.nutrient_id)


def query_nutrient_without_seeking_spore(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE NOT (nutrient)<-[:SOUGHT]-(:Spore)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(nutrient)
            AND NOT (nutrient)-[:STOPPED_BY]->(:Stop)
        RETURN elementId(nutrient)
        LIMIT 10
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(nutrient_id=record[0])
    return engagement_data
