import traceback

from loguru import logger
from neo4j import AsyncGraphDatabase

from mycelium.graph import (create_spore, create_region, query_region_id, create_site, \
                            query_nutrients, connect_region_to_nutrient, query_unexplored_region, fuse_regions,
                            terminate_region,
                            create_digest, \
                            query_spores, query_spore, query_fusion, query_nutrient_context)
from mycelium.inference import extract_relevant_urls, determine_relevance, generate_digest, generate_spore
from mycelium.web import search, scrape, trim_url


class Hypha:
    def __init__(self, graph: AsyncGraphDatabase.driver, fungi_id: str, spore_id: str):
        self.graph = graph
        self.fungi_id = fungi_id
        self.spore_id = spore_id
        self.finished = False
        self.query = None

    async def async_init(self):
        self.query = await query_spore(self.graph, self.spore_id)
        urls = await search(self.query)
        for url in urls:
            await self.create_or_fuse_region(url, self.spore_id)

    async def create_or_fuse_region(self, url, source_id):
        trimmed_url = trim_url(url)
        existing_region_id = await query_region_id(self.graph, trimmed_url)
        if existing_region_id is not None:
            logger.info(f"region already exists: {trimmed_url}")
            await fuse_regions(self.graph, source_id, existing_region_id)
        else:
            logger.info(f"creating new region: {url}")
            await create_region(self.graph, trimmed_url, source_id)

    async def explore_region(self, region_id, url):
        try:
            logger.info(f"exploring region: {url}")
            web_content = await scrape(url)
            if web_content is None:
                logger.warning(f"could not collect content, terminating region: {url}")
                await terminate_region(self.graph, region_id)
                return

            await create_site(self.graph, region_id, url, web_content)
            nutrients = await query_nutrients(self.graph)
            any_relevance = False
            for nutrient_id, topic in nutrients.items():
                relevant = await determine_relevance(topic, web_content)
                if relevant:
                    any_relevance = True
                    logger.info(f"found relevant content for {topic} at {url}")
                    await connect_region_to_nutrient(self.graph, region_id, nutrient_id)
                    relevant_urls = await extract_relevant_urls(self.query, web_content)
                    for relevant_url in set(relevant_urls):
                        await self.create_or_fuse_region(relevant_url, region_id)
                    digest = await generate_digest(topic, web_content)
                    await create_digest(self.graph, region_id, digest, nutrient_id)
                    if await query_fusion(self.graph, region_id):
                        spores = await query_spores(self.graph, self.fungi_id)
                        existing_search_queries = list(spores.values())
                        context_entries = await query_nutrient_context(self.graph, nutrient_id)
                        context = "\n\n".join(context_entries)
                        spore_query = await generate_spore(topic, existing_search_queries, digest, context)
                        await create_spore(self.graph, spore_query, region_id)
            if not any_relevance:
                logger.info(f"no relevant content at {url}")
                await terminate_region(self.graph, region_id)
        except KeyboardInterrupt:
            raise
        except Exception as error:
            logger.error(f"error exploring region, terminating: {error}\n{traceback.format_exc()}")
            await terminate_region(self.graph, region_id)

    async def spread(self):
        logger.info(f"spreading")
        region_id, region_url = await query_unexplored_region(self.graph, self.spore_id)
        if region_id is None:
            logger.info(f"nothing more to explore, finished")
            self.finished = True
            return
        await self.explore_region(region_id, region_url)
