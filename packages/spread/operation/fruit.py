from freeflock_contraptions.framework import Operation
from freeflock_contraptions.inference import OpenaiInference
from pydantic import BaseModel

from communal.graph import query_relevant_claims, create_fruit

inference_client = OpenaiInference()


class EngagementData(BaseModel):
    nutrient_id: str
    nutrient_topic: str


class Fruit(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "fruit")

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_nutrient_with_stop_node(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.nutrient_id
        else:
            return None

    async def act_on_engaged_node(self):
        claims = await query_relevant_claims(self.graph, self.engagement_data.nutrient_id)
        collation = await collate_claims(self.engagement_data.nutrient_topic, claims)
        create_fruit(self.graph, self.engagement_data.nutrient_id, collation)


def query_nutrient_with_stop_node(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE (nutrient)-[:STOPPED_BY]->(:Stop)
            AND NOT (nutrient)-[:FRUITED]->(:Fruit)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(nutrient)
        RETURN elementId(nutrient), nutrient.topic
        LIMIT 10
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(nutrient_id=record[0], nutrient_topic=record[1])
    return engagement_data


class CollationResult(BaseModel):
    collation: str


async def collate_claims(research_topic, claims):
    system_prompt = f"""
Collate a collection of claims on a research topic into a single cohesive whole.
The collated output should contain all relevant information from the provided claims.
The research topic should be the focus of the output.
Include all citations for each claim in the collated output.
"""
    user_prompt = f"""
**Research Topic**
{research_topic}

**Claims**
{claims}
"""
    result = await inference_client.infer_json(
        model_name="o3-mini",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        reasoning_effort="medium",
        response_format=CollationResult)
    return result.collation
