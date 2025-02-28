from asyncio import sleep

from loguru import logger
from openai import AsyncOpenAI
from pydantic import BaseModel

from communal.graph import (query_spore_with_fewer_than_max_regions, engage,
                            query_nutrient_topic_and_context_from_spore, \
                            disengage, create_initial_region)
from spread.operation.framework import OperationName

inference_client = AsyncOpenAI()
MAX_INITIAL_REGIONS = 3


async def add_region_to_spore(graph, engagement_handle):
    operation_name = OperationName.add_region_to_spore
    logger.info("querying spore without region")
    spore_id = query_spore_with_fewer_than_max_regions(graph, MAX_INITIAL_REGIONS, operation_name)
    if spore_id is None:
        logger.info("no spore without region")
        await sleep(1)
        return False
    else:
        logger.info("found spore without region")
    successfully_engaged = engage(graph, spore_id, engagement_handle, operation_name)
    if not successfully_engaged:
        return False
    try:
        research_topic, context = query_nutrient_topic_and_context_from_spore(graph, spore_id)
        inquiry = await generate_initial_inquiry(research_topic, context)
        logger.info(f"generated initial inquiry: {inquiry}")
        create_initial_region(graph, spore_id, inquiry)
        logger.info("created region")
        return True
    finally:
        disengage(graph, spore_id, operation_name)


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
