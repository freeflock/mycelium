from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import query_spore_without_region, engage, query_nutrient_topic_and_context_from_spore, \
    disengage, create_initial_region
from spread.operation.framework import looping_operation

inference_client = AsyncOpenAI()


@looping_operation
async def add_region_to_spore(graph, engagement_handle):
    logger.info("querying spore without region")
    spore_id = await query_spore_without_region(graph)
    if spore_id is None:
        logger.info("no spore without region")
        return False
    else:
        logger.info("found spore without region")
    engagement_id = await engage(graph, spore_id, engagement_handle)
    if engagement_id is None:
        return False
    try:
        research_topic, context = await query_nutrient_topic_and_context_from_spore(graph, spore_id)
        inquiry = await generate_initial_inquiry(research_topic, context)
        logger.info(f"generated initial inquiry: {inquiry}")
        await create_initial_region(graph, spore_id, inquiry)
        logger.info("created region")
        await disengage(graph, engagement_handle)
        return True
    finally:
        await disengage(graph, engagement_handle)


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
