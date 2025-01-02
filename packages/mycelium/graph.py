from random import choice


async def create_fungi(graph):
    response = await graph.execute_query(
        """
        CREATE (fungi:Fungi)
        RETURN elementId(fungi)
        """)
    return response.records[0][0]


async def create_spore(graph, query, source_id):
    response = await graph.execute_query(
        """
        MATCH (source)
        WHERE elementId(source) = $source_id
        CREATE (source)-[:SPORED]->(spore:Spore {query: $query})
        RETURN elementId(spore)
        """,
        query=query,
        source_id=source_id)
    return response.records[0][0]


async def fuse_regions(graph, source_id, target_id):
    await graph.execute_query(
        """
        MATCH (source), (target)
        WHERE elementId(source) = $source_id AND elementId(target) = $target_id
        CREATE (source)-[:FUSED]->(target)
        """,
        source_id=source_id,
        target_id=target_id)


async def create_digest(graph, source_id, digest_content, nutrient_id):
    await graph.execute_query(
        """
        MATCH (source)
        WHERE elementId(source) = $source_id
        MATCH (nutrient:Nutrient)
        WHERE elementId(nutrient) = $nutrient_id
        CREATE (source)-[:DESCRIBED_BY]->(digest:Digest {content: $content})-[:DIGESTS]->(nutrient)
        """,
        source_id=source_id,
        content=digest_content,
        nutrient_id=nutrient_id)


async def create_region(graph, url, source_id):
    await graph.execute_query(
        """
        MATCH (source)
        WHERE elementId(source) = $source_id
        CREATE (source)-[:SPREADS]->(region:Region {url: $url})
        """,
        source_id=source_id,
        url=url)


async def create_site(graph, region_id, url, content):
    await graph.execute_query(
        """
        MATCH (region:Region)
        WHERE elementId(region) = $region_id
        CREATE (region)-[:COLLECTED]->(site:Site {url: $url, content: $content})
        """,
        region_id=region_id,
        url=url,
        content=content)


async def terminate_region(graph, region_id):
    await graph.execute_query(
        """
        MATCH (region:Region)
        WHERE elementId(region) = $region_id
        CREATE (region)-[:SPREADS]->(:Terminus)
        """,
        region_id=region_id)


async def connect_region_to_nutrient(graph, region_id, nutrient_id):
    await graph.execute_query(
        """
        MATCH (region:Region), (nutrient:Nutrient)
        WHERE elementId(region) = $region_id AND elementId(nutrient) = $nutrient_id
        CREATE (region)-[:SPREADS]->(nutrient)
        """,
        region_id=region_id,
        nutrient_id=nutrient_id)


async def query_unexplored_region(graph, source_id):
    response = await graph.execute_query(
        """
        MATCH (source)-[:SPREADS*]->(region:Region)
        WHERE elementId(source) = $source_id
            AND NOT (region)-[:SPREADS]->(:Terminus)
            AND NOT (region)-[:SPREADS]->(:Nutrient)
        RETURN elementId(region), region.url
        """,
        source_id=source_id)
    if len(response.records) == 0:
        return None, None
    record_choice = choice(response.records)
    return record_choice[0], record_choice[1]


async def query_region_id(graph, url):
    response = await graph.execute_query(
        """
        MATCH (region:Region)
        WHERE region.url = $url
        RETURN elementId(region)
        """,
        url=url)
    if len(response.records) == 0:
        return None
    return response.records[0][0]


async def query_spore(graph, spore_id):
    response = await graph.execute_query(
        """
        MATCH (spore:Spore)
        WHERE elementId(spore) = $spore_id
        RETURN spore.query
        """,
        spore_id=spore_id)
    return response.records[0][0]


async def query_spores(graph, fungi_id):
    response = await graph.execute_query(
        """
        MATCH (fungi:Fungi)-[:SPREADS|SPORED*]->(spore:Spore)
        WHERE elementId(fungi) = $fungi_id
        RETURN elementId(spore), spore.query
        """,
        fungi_id=fungi_id)
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


async def query_nutrients(graph):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        RETURN elementId(nutrient), nutrient.topic
        """)
    return {record[0]: record[1] for record in response.records}


async def query_nutrient_topic(graph, nutrient_id):
    response = await graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE elementId(nutrient) = $nutrient_id
        RETURN nutrient.topic
        """,
        nutrient_id=nutrient_id)
    return response.records[0][0]


async def query_fusion(graph, source_id):
    response = await graph.execute_query(
        """
        MATCH (source)-[:FUSED]-(target)
        WHERE elementId(source) = $source_id
        return elementId(target)
        """,
        source_id=source_id)
    if len(response.records) == 0:
        return False
    return True
