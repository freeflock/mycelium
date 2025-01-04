import asyncio
import os
import traceback
from asyncio import TaskGroup
from time import sleep

from loguru import logger
from neo4j import AsyncGraphDatabase

from mycelium.graph import query_nutrients
from mycelium.spread.fungi import Fungi

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")

MIN_HYPHAL_COUNT = 1


async def main():
    while True:
        try:
            async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
                nutrients = await query_nutrients(graph)
                fungi = []
                if len(nutrients.keys()) > 0:
                    for nutrient_id in nutrients.keys():
                        fungus = Fungi(graph, nutrient_id, MIN_HYPHAL_COUNT)
                        fungi.append(fungus)
                    async with TaskGroup() as task_group:
                        for fungus in fungi:
                            task_group.create_task(fungus.async_init())
                    while True:
                        async with TaskGroup() as task_group:
                            for fungus in fungi:
                                task_group.create_task(fungus.grow())
                else:
                    logger.info("no nutrients found")
                    sleep(3)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
