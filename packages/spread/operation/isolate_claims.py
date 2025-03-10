from typing import List

from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import create_claim
from spread.operation.framework import Operation

inference_client = AsyncOpenAI()


class EngagementData(BaseModel):
    region_id: str
    finding_content: str
    finding_citations: List[str]


class IsolateClaims(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "isolate_claims")
        self.engagement_data = None

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_finding_without_claims(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.region_id
        else:
            return None

    async def act_on_engaged_node(self):
        claims = await generate_claims(self.engagement_data.finding_content, self.engagement_data.finding_citations)
        for claim in claims:
            claim_content = claim.content
            claim_citations = claim.citations
            create_claim(self.graph, self.engagement_data.region_id, claim_content, claim_citations)


def query_finding_without_claims(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        MATCH (region:Region)-[:FOUND]->(finding:Finding)
        WHERE elementId(nutrient) = finding.nutrient_id
            AND NOT (nutrient)-[:STOPPED_BY]->(:Stop)
            AND NOT (region)-[:CLAIMED]->(:Claim)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(region)
        RETURN elementId(region), finding.content, finding.citations
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(region_id=record[0], finding_content=record[1], finding_citations=record[2])
    return engagement_data


class ClaimsResult(BaseModel):
    class Claim(BaseModel):
        content: str
        citations: List[str]

    claims: List[Claim]


async def generate_claims(finding_content, citations):
    completion = await inference_client.beta.chat.completions.parse(
        response_format=ClaimsResult,
        messages=[
            {
                "role": "system",
                "content": f"""
Given some content, and a list of citations, come up with a list of claims made in the content.
Include all claims made in the content which include a citation.
Do not include any claims which do not have a citation.
Each claim should fully encapsulate the pertinent information presented in the content.
Each claim should include enough context for the claim to be understood by itself.
Each claim should be unique.

Citations are provided in brackets after a claim, and correspond to the index of the url in the provided citation list.

-- example --
**Content**
This is an example claim![3][2]

**Citations**
["https://www.first_example_url.com", "https://www.second_example_url.com", "https://www.third_example_url.com"]
-- end example --

Indicates the claim "This is an example claim!" includes citations:
"https://www.third_example_url.com" and "https://www.second_example_url.com"
""",
            },
            {
                "role": "user",
                "content": f"""
**Content**
{finding_content}

**Citations**
{citations}
    """
            }
        ],
        model="o3-mini",
    )
    return completion.choices[0].message.parsed.claims
