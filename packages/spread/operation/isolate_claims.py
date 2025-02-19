from typing import List

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import engage, disengage, query_finding_without_claims, create_claim
from spread.operation.framework import looping_operation

inference_client = AsyncOpenAI()


@looping_operation
async def isolate_claims(graph, engagement_handle):
    logger.info("querying finding without claims")
    region_id, finding_content, citations = await query_finding_without_claims(graph)
    if region_id is None:
        logger.info("no finding without claims")
        return False
    else:
        logger.info("found finding without claims")
    engagement_id = await engage(graph, region_id, engagement_handle)
    if engagement_id is None:
        return False
    try:
        claims = await generate_claims(finding_content, citations)
        logger.info("generated claims")
        for claim in claims:
            claim_content = claim.content
            claim_citations = claim.citations
            await create_claim(graph, region_id, claim_content, claim_citations)
            logger.info("created claim")
        return True
    finally:
        await disengage(graph, engagement_handle)


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
Do not include any information beyond what is presented in the content.
Include all claims made in the content which include a citation.
Do not include any claims which do not have a citation.
Each claim should fully encapsulate the pertinent information presented in the content.
Each claim should include all relevant context required for the claim to stand alone.
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
