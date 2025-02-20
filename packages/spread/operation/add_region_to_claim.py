from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import engage, disengage, create_region, query_nutrient_topic_and_context_from_claim, \
    query_relevant_claim_without_region

inference_client = AsyncOpenAI()


async def add_region_to_claim(graph, engagement_handle):
    logger.info("querying relevant claim without region")
    source_claim_id, claim_content, source_region_id = await query_relevant_claim_without_region(graph)
    if source_claim_id is None:
        logger.info("no relevant claim without region")
        return False
    else:
        logger.info("found relevant claim without region")
    engagement_id = await engage(graph, source_claim_id, engagement_handle)
    if engagement_id is None:
        return False
    try:
        research_topic, context = await query_nutrient_topic_and_context_from_claim(graph, source_claim_id)
        inquiry = await generate_inquiry_from_claim(research_topic, context, claim_content)
        logger.info(f"generated inquiry: {inquiry}")
        await create_region(graph, source_region_id, source_claim_id, inquiry)
        logger.info("created region")
        return True
    finally:
        await disengage(graph, engagement_handle)


class InquiryResult(BaseModel):
    inquiry: str


async def generate_inquiry_from_claim(research_topic, context, claim):
    completion = await inference_client.beta.chat.completions.parse(
        response_format=InquiryResult,
        messages=[
            {
                "role": "system",
                "content": f"""
Given a research topic, some context related to the research topic, and a claim made about the research topic,
come up with an inquiry that can be used to collect more information on the research topic.
The inquiry should seek to broaden understanding of the research topic.
The inquiry should address some missing piece of information.
The inquiry should be related to the provided claim.
""",
            },
            {
                "role": "user",
                "content": f"""

**Research Topic**
{research_topic}

**Context**
{context}

**Claim**
{claim}
"""
            }
        ],
        model="o3-mini",
    )
    return completion.choices[0].message.parsed.inquiry
