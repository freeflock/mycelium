import logging
import os

from fastapi import FastAPI
from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI
from pydantic import BaseModel
from starlette.responses import JSONResponse

from communal.api_framework import ApiKeyValidator

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

inference_client = AsyncOpenAI()

app = FastAPI()
app.add_middleware(ApiKeyValidator)


class NutrientRequest(BaseModel):
    research_topic: str
    category: str
    context: str


async def create_nutrient(graph, research_topic, category, context):
    response = await graph.execute_query(
        """
        CREATE (nutrient:Nutrient {topic: $research_topic, category: $category})
        CREATE (context:Context {content: $context})
        CREATE (nutrient)-[:DESCRIBED_BY]->(context)
        RETURN elementId(nutrient) as nutrient_id
        """,
        research_topic=research_topic,
        category=category,
        context=context)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    nutrient_id = record["nutrient_id"]
    return nutrient_id


@app.post("/provide_nutrient")
async def provide_nutrient(nutrient_request: NutrientRequest):
    logger.info(f"providing nutrient: {nutrient_request}")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        nutrient_id = await create_nutrient(graph,
                                            nutrient_request.research_topic,
                                            nutrient_request.category,
                                            nutrient_request.context)
        if nutrient_id is None:
            return JSONResponse(status_code=500, content={"message": "Failed to create nutrient"})
        return JSONResponse(status_code=200, content={"nutrient_id": nutrient_id})


async def query_all_relationships(graph):
    response = await graph.execute_query(
        """
        MATCH (s)-[r]->(t)
        RETURN id(s) as source, LABELS(s) as source_labels, id(t) as target, LABELS(t) as target_labels, type(r) as 
        relationship
        """)
    return response.records


@app.post("/visualize")
async def visualize():
    logger.info(f"visualize called")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        all_relationships = await query_all_relationships(graph)
        nodes_with_labels = {}
        links = []
        for relationship in all_relationships:
            nodes_with_labels[relationship["source"]] = relationship["source_labels"][0]
            nodes_with_labels[relationship["target"]] = relationship["target_labels"][0]
            links.append({"source": relationship["source"],
                          "target": relationship["target"],
                          "name": relationship["relationship"]})
        nodes = [{"id": node_id, "name": name} for node_id, name in nodes_with_labels.items()]
        result = {"nodes": nodes, "links": links}
    return JSONResponse(status_code=200, content={"graph_data": result})
