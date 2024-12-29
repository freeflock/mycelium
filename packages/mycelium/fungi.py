import asyncio
from random import choice

from neo4j import AsyncGraphDatabase

from mycelium.graph import query_nutrients, query_spores, create_spore, create_fungi
from mycelium.hypha import Hypha
from mycelium.inference import generate_search_query


class Fungi:
    def __init__(self, graph: AsyncGraphDatabase.driver, min_hyphal_count: int):
        self.min_hyphal_count = min_hyphal_count
        self.hyphae = []
        self.graph = graph
        self.fungi_id = None

    async def async_init(self):
        self.fungi_id = await create_fungi(self.graph)
        await self.produce_hyphae()

    async def produce_hypha(self, spore_id):
        hypha = Hypha(self.graph, spore_id)
        await hypha.async_init()
        self.hyphae.append(hypha)

    async def produce_hyphae(self):
        while len(self.hyphae) < self.min_hyphal_count:
            nutrients = await query_nutrients(self.graph)
            nutrient_id = choice(list(nutrients.keys()))
            spores = await query_spores(self.graph)
            existing_queries = list(spores.values())
            query = await generate_search_query(nutrients.get(nutrient_id), existing_queries)
            spore_id = await create_spore(self.graph, query, self.fungi_id)
            await self.produce_hypha(spore_id)

    async def sprout_spores(self):
        spores = await query_spores(self.graph)
        hyphal_queries = [hypha.query for hypha in self.hyphae]
        cleaned_spores = {spore_id: query for spore_id, query in spores.items() if query not in hyphal_queries}
        for spore_id in list(cleaned_spores.keys()):
            await self.produce_hypha(spore_id)

    async def prune_hyphae(self):
        hypha_to_remove = []
        for index, hypha in enumerate(self.hyphae):
            if hypha.finished:
                hypha_to_remove.append(index)
        for index in hypha_to_remove:
            self.hyphae.pop(index)

    async def grow(self):
        await self.sprout_spores()
        await self.prune_hyphae()
        await self.produce_hyphae()
        async with asyncio.TaskGroup() as task_group:
            for hypha in self.hyphae:
                task_group.create_task(hypha.spread())
