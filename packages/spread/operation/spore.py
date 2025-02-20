from loguru import logger

from communal.graph import query_nutrient_without_seeking_spore, engage, create_spore, disengage


async def spore(graph, engagement_handle):
    logger.info("querying nutrient without seeking spore")
    nutrient_id = await query_nutrient_without_seeking_spore(graph)
    if nutrient_id is None:
        logger.info("no nutrient without seeking spore")
        return False
    else:
        logger.info("found nutrient without seeking spore")
    successfully_engaged = await engage(graph, nutrient_id, engagement_handle)
    if not successfully_engaged:
        return False
    try:
        await create_spore(graph, nutrient_id)
        logger.info("created spore")
        return True
    finally:
        await disengage(graph, nutrient_id)
