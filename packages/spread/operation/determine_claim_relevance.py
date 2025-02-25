from asyncio import sleep

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import query_claim_without_relevance_or_terminus, engage, query_all_nutrients, \
    bind_claim_to_nutrient, create_terminus, disengage

inference_client = AsyncOpenAI()
OPERATION_NAME = "determine_claim_relevance"


async def determine_claim_relevance(graph, engagement_handle):
    logger.info("querying claim without relevance or terminus")
    claim_id, claim_content = query_claim_without_relevance_or_terminus(graph, OPERATION_NAME)
    if claim_id is None:
        logger.info("no claim without relevance or terminus")
        await sleep(1)
        return False
    else:
        logger.info("found claim without relevance or terminus")
    successfully_engaged = engage(graph, claim_id, engagement_handle, OPERATION_NAME)
    if not successfully_engaged:
        return False
    try:
        nutrients = query_all_nutrients(graph)
        relevant_to_at_least_one = False
        for nutrient_id, research_topic in nutrients.items():
            relevant = await determine_relevance(research_topic, claim_content)
            if relevant:
                bind_claim_to_nutrient(graph, claim_id, nutrient_id)
                logger.info(f"bound claim to nutrient: {research_topic}")
                relevant_to_at_least_one = True
            else:
                logger.info(f"claim not relevant to nutrient: {research_topic}")
        if not relevant_to_at_least_one:
            logger.info("claim not relevant to any nutrient")
            create_terminus(graph, claim_id)
        return True
    finally:
        disengage(graph, claim_id, OPERATION_NAME)


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
