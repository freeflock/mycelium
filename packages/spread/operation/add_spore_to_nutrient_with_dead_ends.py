from freeflock_contraptions.framework import Operation
from freeflock_contraptions.inference import OpenaiInference
from pydantic import BaseModel

from communal.graph import create_spore

inference_client = OpenaiInference()


class EngagementData(BaseModel):
    nutrient_id: str


class AddSporeToNutrientWithDeadEnds(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "add_spore_to_nutrient_with_dead_ends")

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_nutrient_with_high_dead_end_ratio(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.nutrient_id
        else:
            return None

    async def act_on_engaged_node(self):
        create_spore(self.graph, self.engagement_data.nutrient_id)


def query_nutrient_with_high_dead_end_ratio(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)<-[:SOUGHT]-(:Spore)-[:SPREAD*]->(region:Region)
        WHERE NOT (nutrient)-[:STOPPED_BY]->(:Stop)
        MATCH (region)-[:CLAIMED]->(claim:Claim)
        OPTIONAL MATCH (claim)-[:TERMINATES]->(terminus:Terminus)
        WHERE NOT (region)-[:SPREAD]->(:Region)
        WITH nutrient, region, count(claim) AS claim_count, count(terminus) AS terminus_count
        WHERE claim_count > 0
          AND claim_count = terminus_count
        WITH nutrient, count(region) AS dead_end_region_count
        MATCH (nutrient)<-[:SOUGHT]-(spore:Spore)
        WITH nutrient, dead_end_region_count, count(spore) AS spore_count
        WHERE ceil(dead_end_region_count * 0.33) > spore_count
        RETURN elementId(nutrient)
        LIMIT 10
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(nutrient_id=record[0])
    return engagement_data
