from asyncio import sleep

from loguru import logger

from communal.graph import engage, disengage, query_inquiry_without_finding, create_finding
from spread.sonar import execute_search


async def collect_finding(graph, engagement_handle):
    logger.info("querying inquiry without finding")
    region_id, inquiry = query_inquiry_without_finding(graph)
    if region_id is None:
        logger.info("no inquiry without finding")
        await sleep(1)
        return False
    else:
        logger.info("found inquiry without finding")
    successfully_engaged = engage(graph, region_id, engagement_handle)
    if not successfully_engaged:
        return False
    try:
        reasoning, content, citations = await execute_search(inquiry)
        logger.info("search succeeded")
        create_finding(graph, region_id, reasoning, content, citations)
        logger.info("created finding")
        return True
    finally:
        disengage(graph, region_id)
