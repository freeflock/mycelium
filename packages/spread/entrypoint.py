import asyncio
import os
import traceback
from asyncio import sleep
from uuid import uuid4

from loguru import logger
from neo4j import AsyncGraphDatabase

from spread.operation.add_region_to_claim import add_region_to_claim
from spread.operation.add_region_to_spore import add_region_to_spore
from spread.operation.collect_finding import collect_finding
from spread.operation.determine_claim_relevance import determine_claim_relevance
from spread.operation.isolate_claims import isolate_claims
from spread.operation.spore import spore

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


async def main():
    engagement_handle = str(uuid4())
    while True:
        try:
            async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
                async with asyncio.TaskGroup() as task_group:
                    task_group.create_task(spore(graph, engagement_handle)),
                    task_group.create_task(add_region_to_spore(graph, engagement_handle)),
                    task_group.create_task(collect_finding(graph, engagement_handle)),
                    task_group.create_task(isolate_claims(graph, engagement_handle)),
                    task_group.create_task(determine_claim_relevance(graph, engagement_handle)),
                    task_group.create_task(add_region_to_claim(graph, engagement_handle))
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"(!) unhandled exception: {error}\n{traceback.format_exc()}")
            await sleep(3)


if __name__ == '__main__':
    asyncio.run(main())
