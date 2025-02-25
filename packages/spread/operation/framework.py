import asyncio
import os
import traceback
from asyncio import sleep

from loguru import logger
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


async def loop_operation(operation, *args, **kwargs):
    while True:
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
            try:
                tasks = set()
                while len(tasks) < 10:
                    task = asyncio.create_task(operation(graph, *args, **kwargs))
                    tasks.add(task)
                    task.add_done_callback(tasks.discard)
                await sleep(1)
            except KeyboardInterrupt:
                raise
            except Exception as error:
                logger.error(f"(!) unhandled exception in loop operation: {error}\n{traceback.format_exc()}")
