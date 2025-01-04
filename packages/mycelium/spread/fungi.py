import asyncio
from asyncio import TaskGroup

from neo4j import AsyncGraphDatabase

from mycelium.graph import query_spores, create_spore, create_fungi, query_nutrient_topic, query_nutrient_context
from mycelium.spread.hypha import Hypha
from mycelium.inference import generate_search_query


class Fungi:
    def __init__(self, graph: AsyncGraphDatabase.driver, primary_nutrient_id: str, min_hyphal_count: int):
        self.min_hyphal_count = min_hyphal_count
        self.hyphae = []
        self.graph = graph
        self.fungi_id = None
        self.primary_nutrient_id = primary_nutrient_id

    async def async_init(self):
        self.fungi_id = await create_fungi(self.graph)
        await self.produce_hyphae()

    async def produce_hypha(self, spore_id):
        hypha = Hypha(self.graph, self.fungi_id, spore_id)
        await hypha.async_init()
        self.hyphae.append(hypha)

    async def create_initial_hypha(self):
        spores = await query_spores(self.graph, self.fungi_id)
        existing_queries = list(spores.values())
        topic = await query_nutrient_topic(self.graph, self.primary_nutrient_id)
        context_entries = await query_nutrient_context(self.graph, self.primary_nutrient_id)
        context = "\n\n".join(context_entries)
        query = await generate_search_query(topic, existing_queries, context)
        spore_id = await create_spore(self.graph, query, self.fungi_id)
        await self.produce_hypha(spore_id)

    async def produce_hyphae(self):
        hypha_to_create = self.min_hyphal_count - len(self.hyphae)
        async with TaskGroup() as task_group:
            for i in range(hypha_to_create):
                task_group.create_task(self.create_initial_hypha())

    async def sprout_spores(self):
        spores = await query_spores(self.graph, self.fungi_id)
        hyphal_queries = [hypha.query for hypha in self.hyphae]
        cleaned_spores = {spore_id: query for spore_id, query in spores.items() if query not in hyphal_queries}
        for spore_id in list(cleaned_spores.keys()):
            await self.produce_hypha(spore_id)

    async def prune_hyphae(self):
        prune_complete = False
        while not prune_complete:
            hypha_to_pop = None
            for index, hypha in enumerate(self.hyphae):
                if hypha.finished:
                    hypha_to_pop = index
                    break
            if hypha_to_pop is None:
                prune_complete = True
            else:
                self.hyphae.pop(hypha_to_pop)

    async def grow(self):
        await self.sprout_spores()
        await self.prune_hyphae()
        await self.produce_hyphae()
        async with asyncio.TaskGroup() as task_group:
            for hypha in self.hyphae:
                task_group.create_task(hypha.spread())
