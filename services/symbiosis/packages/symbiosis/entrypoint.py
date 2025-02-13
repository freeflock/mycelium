import logging
import os

from fastapi import FastAPI
from langchain import hub
from langchain_openai import ChatOpenAI
from neo4j import AsyncGraphDatabase
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

gpt_o1 = ChatOpenAI(model="o1-preview", temperature=1)


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


async def create_nutrient(graph, research_topic, category, context):
    await graph.execute_query(
        """
        CREATE (nutrient:Nutrient {topic: $research_topic, category: $category})
        CREATE (context:Context {content: $context})
        CREATE (nutrient)-[:DESCRIBED_BY]->(context)
        """,
        research_topic=research_topic,
        category=category,
        context=context)


@app.post("/clear")
async def clear():
    logger.info(f"clearing graph")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        await clear_graph(graph)


async def clear_graph(graph):
    await graph.execute_query(
        """
        MATCH (n)
        DETACH DELETE n
        """)


@app.post("/fruit")
async def fruit():
    logger.info(f"fruiting")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        nutrients = await query_nutrients(graph)
        nutrient_id = list(nutrients.keys())[0]
        topic = nutrients.get(nutrient_id)
        digests = await query_digests(graph, nutrient_id)
        collation = await collate_reports(topic, digests)
        return {"collation": collation}


async def query_nutrients(graph):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        RETURN elementId(nutrient), nutrient.topic
        """)
    return {record[0]: record[1] for record in response.records}


async def query_digests(graph, nutrient_id):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)<-[:SPREADS]-(region:Region)-[:DESCRIBED_BY]->(digest:Digest)
        WHERE elementId(nutrient) = $nutrient_id
        RETURN digest.content
        """,
        nutrient_id=nutrient_id)
    if len(response.records) == 0:
        return None
    return [record[0] for record in response.records]


async def collate_reports(research_topic, digests):
    prompt = hub.pull("vagabond/mycelium_collation")
    chain = prompt | gpt_o1
    output = await chain.ainvoke({"research_topic": research_topic, "reports": digests})
    return output.content


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


async def query_all_relationships(graph):
    response = await graph.execute_query(
        """
        MATCH (s)-[r]->(t)
        RETURN id(s) as source, LABELS(s) as source_labels, id(t) as target, LABELS(t) as target_labels, type(r) as 
        relationship
        """)
    return response.records
