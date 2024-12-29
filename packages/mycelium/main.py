import asyncio
import os
import traceback
from time import sleep

from loguru import logger
from neo4j import AsyncGraphDatabase

from mycelium.fungi import Fungi

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")

MIN_HYPHAL_COUNT = 5


async def main():
    while True:
        try:
            async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
                fungi = Fungi(graph, MIN_HYPHAL_COUNT)
                await fungi.async_init()
                while True:
                    await fungi.grow()
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
