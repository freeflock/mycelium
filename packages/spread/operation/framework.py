import asyncio
import os
import traceback
from asyncio import sleep
from enum import StrEnum

from loguru import logger
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


class OperationName(StrEnum):
    add_region_to_claim = "add_region_to_claim"
    add_region_to_spore = "add_region_to_spore"
    collect_finding = "collect_finding"
    determine_claim_relevance = "determine_claim_relevance"
    isolate_claims = "isolate_claims"
    spore = "spore"


async def loop_operation(operation, *args, **kwargs):
    with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        while True:
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
