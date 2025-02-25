from asyncio import sleep

from loguru import logger

from communal.graph import query_nutrient_without_seeking_spore, engage, create_spore, disengage

OPERATION_NAME = "spore"


async def spore(graph, engagement_handle):
    logger.info("querying nutrient without seeking spore")
    nutrient_id = query_nutrient_without_seeking_spore(graph, OPERATION_NAME)
    if nutrient_id is None:
        logger.info("no nutrient without seeking spore")
        await sleep(1)
        return False
    else:
        logger.info("found nutrient without seeking spore")
    successfully_engaged = engage(graph, nutrient_id, engagement_handle, OPERATION_NAME)
    if not successfully_engaged:
        return False
    try:
        create_spore(graph, nutrient_id)
        logger.info("created spore")
        return True
    finally:
        disengage(graph, nutrient_id, OPERATION_NAME)
