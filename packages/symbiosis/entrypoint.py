import logging
import os

from fastapi import FastAPI
from neo4j import AsyncGraphDatabase
from openai import AsyncOpenAI
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from communal.graph import clear_graph, create_nutrient, query_all_relationships, query_all_nutrients, query_claims

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

inference_client = AsyncOpenAI()


class ApiKeyValidator(BaseHTTPMiddleware):
    def __init__(self, app):
        self.api_key = os.getenv("SYMBIOSIS_API_KEY")
        super().__init__(app)

    async def dispatch(self, request, call_next):
        request_key = request.headers.get("x-api-key")
        if request_key == self.api_key:
            return await call_next(request)
        else:
            return JSONResponse(status_code=403, content={})


app = FastAPI()
app.add_middleware(ApiKeyValidator)


class NutrientRequest(BaseModel):
    research_topic: str
    category: str
    context: str


@app.post("/provide_nutrient")
async def provide_nutrient(nutrient_request: NutrientRequest):
    logger.info(f"providing nutrient: {nutrient_request}")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        await create_nutrient(graph,
                              nutrient_request.research_topic,
                              nutrient_request.category,
                              nutrient_request.context)


@app.post("/clear")
async def clear():
    logger.info(f"clearing graph")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        await clear_graph(graph)


@app.post("/fruit")
async def fruit():
    logger.info(f"fruiting")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        nutrients = await query_all_nutrients(graph)
        nutrient_id = list(nutrients.keys())[0]
        topic = nutrients.get(nutrient_id)
        claims = await query_claims(graph, nutrient_id)
        if claims is not None:
            collation = await collate_claims(topic, claims)
        else:
            collation = None
        return {"collation": collation}


async def collate_claims(research_topic, claims):
    completion = await inference_client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": f"""
Collate a collection of claims on a research topic into a single cohesive whole.
The collated output should contain all relevant information from the provided claims.
The research topic should be the focus of the output.
Include all citations for each claim in the collated output.

**Research Topic**
{research_topic}

**Claims**
{claims}
""",
            }
        ],
        model="o1",
    )
    return completion.choices[0].message


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
