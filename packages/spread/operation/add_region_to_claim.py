from freeflock_contraptions.framework import Operation
from freeflock_contraptions.inference import OpenaiInference
from pydantic import BaseModel

from communal.graph import create_region, query_nutrient_topic_and_context_from_claim

inference_client = OpenaiInference()


class EngagementData(BaseModel):
    source_claim_id: str
    claim_content: str
    source_region_id: str


class AddRegionToClaim(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "add_region_to_claim")

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_relevant_claim_without_region(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.source_claim_id
        else:
            return None

    async def act_on_engaged_node(self):
        research_topic, context = query_nutrient_topic_and_context_from_claim(self.graph,
                                                                              self.engagement_data.source_claim_id)
        inquiry = await generate_inquiry_from_claim(research_topic, context, self.engagement_data.claim_content)
        create_region(self.graph, self.engagement_data.source_region_id, self.engagement_data.source_claim_id, inquiry)


def query_relevant_claim_without_region(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (nutrient: Nutrient)
        MATCH (claim:Claim)<-[:CLAIMED]-(region:Region)
        WHERE NOT (nutrient)-[:STOPPED_BY]->(:Stop)
            AND (claim)-[:RELEVANT_TO]->(:Nutrient)
            AND NOT (claim)-[:INFORMED]->(:Region)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(claim)
        RETURN elementId(claim), claim.content, elementId(region)
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(source_claim_id=record[0], claim_content=record[1], source_region_id=record[2])
    return engagement_data


class InquiryResult(BaseModel):
    inquiry: str


async def generate_inquiry_from_claim(research_topic, context, claim):
    system_prompt = f"""
Given a research topic, some context related to the research topic, and a claim made about the research topic,
come up with an inquiry that can be used to collect more information on the research topic.
The inquiry should seek to broaden understanding of the research topic.
The inquiry should address some missing piece of information.
The inquiry should be related to the provided claim.
"""
    user_prompt = f"""
**Research Topic**
{research_topic}

**Context**
{context}

**Claim**
{claim}
"""
    result = await inference_client.infer_json(
        model_name="o3-mini",
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        reasoning_effort="medium",
        response_format=InquiryResult)
    return result.inquiry
