from asyncio import sleep

from loguru import logger

from communal.graph import query_nutrient_without_seeking_spore, engage, create_spore, disengage
from spread.operation.framework import OperationName


async def spore(graph, engagement_handle):
    operation_name = OperationName.spore
    logger.info("querying nutrient without seeking spore")
    nutrient_id = query_nutrient_without_seeking_spore(graph, operation_name)
    if nutrient_id is None:
        logger.info("no nutrient without seeking spore")
        await sleep(1)
        return False
    else:
        logger.info("found nutrient without seeking spore")
    successfully_engaged = engage(graph, nutrient_id, engagement_handle, operation_name)
    if not successfully_engaged:
        return False
    try:
        create_spore(graph, nutrient_id)
        logger.info("created spore")
        return True
    finally:
        disengage(graph, nutrient_id, operation_name)
