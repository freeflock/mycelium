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
    await graph.execute_query(
        """
        CREATE (nutrient:Nutrient {topic: $research_topic, category: $category})
        CREATE (context:Context {content: $context})
        CREATE (nutrient)-[:DESCRIBED_BY]->(context)
        """,
        research_topic=research_topic,
        category=category,
        context=context)


@app.post("/provide_nutrient")
async def provide_nutrient(nutrient_request: NutrientRequest):
    logger.info(f"providing nutrient: {nutrient_request}")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        await create_nutrient(graph,
                              nutrient_request.research_topic,
                              nutrient_request.category,
                              nutrient_request.context)


async def clear_graph(graph):
    await graph.execute_query(
        """
        MATCH (n)
        DETACH DELETE n
        """)


@app.post("/clear")
async def clear():
    logger.info(f"clearing graph")
    async with AsyncGraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as graph:
        await clear_graph(graph)


async def query_all_nutrients(graph):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        RETURN elementId(nutrient), nutrient.topic
        """)
    return {record[0]: record[1] for record in response.records}


async def query_claims(graph, nutrient_id):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)<-[:RELEVANT_TO]-(claim:Claim)
        WHERE elementId(nutrient) = $nutrient_id
        RETURN claim.content, claim.citations
        """,
        nutrient_id=nutrient_id)
    if len(response.records) == 0:
        return None
    return [{"claim_content": record[0], "claim_citations": record[1]} for record in response.records]


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
