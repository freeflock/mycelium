from loguru import logger

from communal.graph import engage, disengage, query_inquiry_without_finding, create_finding
from spread.sonar import execute_search


async def collect_finding(graph, engagement_handle):
    logger.info("querying inquiry without finding")
    region_id, inquiry = await query_inquiry_without_finding(graph)
    if region_id is None:
        logger.info("no inquiry without finding")
        return False
    else:
        logger.info("found inquiry without finding")
    engagement_id = await engage(graph, region_id, engagement_handle)
    if engagement_id is None:
        return False
    try:
        reasoning, content, citations = await execute_search(inquiry)
        logger.info("search succeeded")
        await create_finding(graph, region_id, reasoning, content, citations)
        logger.info("created finding")
        return True
    finally:
        await disengage(graph, engagement_handle)
