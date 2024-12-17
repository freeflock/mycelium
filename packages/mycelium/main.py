import asyncio
import os
import traceback
from time import sleep

from langchain_neo4j import Neo4jGraph
from loguru import logger

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


async def spread(graph):
    logger.info(f"spread called")


async def recurse(graph):
    while True:
        await spread(graph)
        sleep(3)


async def main():
    while True:
        try:
            graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
            await recurse(graph)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
