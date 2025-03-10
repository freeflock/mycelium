from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import query_nutrient_topic_and_context_from_spore, create_initial_region
from spread.operation.framework import Operation

inference_client = AsyncOpenAI()


class EngagementData(BaseModel):
    spore_id: str


class AddRegionToSpore(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "add_region_to_spore")
        self.engagement_data = None
        self.max_initial_regions = 3

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_spore_with_fewer_than_max_regions(self.graph, self.operation_name,
                                                                       self.max_initial_regions)
        if self.engagement_data is not None:
            return self.engagement_data.spore_id
        else:
            return None

    async def act_on_engaged_node(self):
        research_topic, context = query_nutrient_topic_and_context_from_spore(self.graph, self.engagement_data.spore_id)
        inquiry = await generate_initial_inquiry(research_topic, context)
        create_initial_region(self.graph, self.engagement_data.spore_id, inquiry)


def query_spore_with_fewer_than_max_regions(graph, operation_name, max_regions):
    response = graph.execute_query(
        """
        MATCH (spore:Spore), (nutrient: Nutrient)
        WHERE elementId(nutrient) = spore.nutrient_id
            AND NOT (nutrient)-[:STOPPED_BY]->(:Stop)
        OPTIONAL MATCH (spore)-[:SPREAD]-(region:Region)
        WITH spore, count(region) AS region_count
        WHERE region_count < $max_regions
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(spore)
        RETURN elementId(spore)
        """,
        max_regions=max_regions,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(spore_id=record[0])
    return engagement_data


class InquiryResult(BaseModel):
    inquiry: str


async def generate_initial_inquiry(research_topic, context):
    completion = await inference_client.beta.chat.completions.parse(
        response_format=InquiryResult,
        messages=[
            {
                "role": "system",
                "content": f"""
Given a research topic and some context related to the topic, phrase the research topic as an inquiry.
Output only the inquiry.
Do not add a prefix or suffix to the inquiry.
    """,
            },
            {
                "role": "user",
                "content": f"""
    **Research Topic**
    {research_topic}

    **Context**
    {context}
    """
            }
        ],
        model="o3-mini",
    )
    return completion.choices[0].message.parsed.inquiry
