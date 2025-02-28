from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import query_all_nutrients, bind_claim_to_nutrient, create_terminus
from spread.operation.framework import Operation

inference_client = AsyncOpenAI()


class EngagementData(BaseModel):
    claim_id: str
    claim_content: str


class DetermineClaimRelevance(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "determine_claim_relevance")
        self.engagement_data = None

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_claim_without_relevance_or_terminus(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.claim_id
        else:
            return None

    async def act_on_engaged_node(self):
        nutrients = query_all_nutrients(self.graph)
        relevant_to_at_least_one = False
        for nutrient_id, research_topic in nutrients.items():
            relevant = await determine_relevance(research_topic, self.engagement_data.claim_content)
            if relevant:
                bind_claim_to_nutrient(self.graph, self.engagement_data.claim_id, nutrient_id)
                relevant_to_at_least_one = True
        if not relevant_to_at_least_one:
            create_terminus(self.graph, self.engagement_data.claim_id)


def query_claim_without_relevance_or_terminus(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (claim:Claim)
        WHERE NOT (claim)-[:TERMINATES]->(:Terminus)
            AND NOT (claim)-[:RELEVANT_TO]->(:Nutrient)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(claim)
        RETURN elementId(claim), claim.content
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(claim_id=record[0], claim_content=record[1])
    return engagement_data


class RelevenceResult(BaseModel):
    claim_is_relevant: bool


async def determine_relevance(research_topic, claim_content):
    completion = await inference_client.beta.chat.completions.parse(
        response_format=RelevenceResult,
        messages=[
            {
                "role": "system",
                "content": f"""
Given a research topic, determine if the provided claim is relevant.
The claim is relevant if the claim is directly related to the research topic,
and contains useful information for pursuing understanding of the research topic.
The claim is not relevant if it is unrelated to the research topic,
or contains little useful information about the research topic.
    """,
            },
            {
                "role": "user",
                "content": f"""
**Research Topic**
{research_topic}

**Claim**
{claim_content}
    """
            }
        ],
        model="o3-mini",
    )
    return completion.choices[0].message.parsed.claim_is_relevant
