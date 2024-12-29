import asyncio
import os

from loguru import logger
from neo4j import AsyncGraphDatabase

from mycelium.graph import query_nutrients, query_digests
from mycelium.inference import collate_reports

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


async def fruit():
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
        nutrients = await query_nutrients(graph)
        nutrient_id = list(nutrients.keys())[0]
        topic = nutrients.get(nutrient_id)
        digests = await query_digests(graph, nutrient_id)
        collation = await collate_reports(topic, digests)
        print(collation)


if __name__ == '__main__':
    asyncio.run(fruit())
