def clear_graph(graph):
    graph.execute_query(
        """
        MATCH (n)
        DETACH DELETE n
        """)


def engage(graph, node_id, engagement_handle):
    response = graph.execute_query(
        """
        MATCH (engagee)
        WHERE elementId(engagee) = $node_id
            AND engagee.engagement IS NULL
        SET engagee.engagement = $engagement_handle
        return TRUE
        """,
        node_id=node_id,
        engagement_handle=engagement_handle)
    if len(response.records) == 0:
        return False
    else:
        return True


def disengage(graph, node_id):
    graph.execute_query(
        """
        MATCH (engagee)
        WHERE elementId(engagee) = $node_id
        REMOVE engagee.engagement
        """,
        node_id=node_id)


def create_nutrient(graph, research_topic, category, context):
    graph.execute_query(
        """
        CREATE (nutrient:Nutrient {topic: $research_topic, category: $category})
        CREATE (context:Context {content: $context})
        CREATE (nutrient)-[:DESCRIBED_BY]->(context)
        """,
        research_topic=research_topic,
        category=category,
        context=context)


def query_all_nutrients(graph):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        RETURN elementId(nutrient), nutrient.topic
        """)
    return {record[0]: record[1] for record in response.records}


def query_nutrient_without_seeking_spore(graph):
    response = graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE NOT (nutrient)<-[:SOUGHT]-(:Spore)
            AND nutrient.engagement IS NULL
        RETURN elementId(nutrient)
        """)
    if len(response.records) == 0:
        return None
    return response.records[0][0]


def create_spore(graph, nutrient_id):
    graph.execute_query(
        """
        MATCH (nutrient:Nutrient)
        WHERE elementId(nutrient) = $nutrient_id
        CREATE (spore:Spore {inquiry: nutrient.topic})
        CREATE (spore)-[:SOUGHT]->(nutrient)
        """,
        nutrient_id=nutrient_id)


def query_spore_with_fewer_than_max_regions(graph, max_regions):
    response = graph.execute_query(
        """
        MATCH (spore:Spore)
        OPTIONAL MATCH (spore)-[:SPREAD]-(region:Region)
        WITH spore, count(region) AS region_count
        WHERE region_count < $max_regions
            AND spore.engagement IS NULL
        RETURN elementId(spore)
        """,
        max_regions=max_regions)
    if len(response.records) == 0:
        return None
    return response.records[0][0]


def query_nutrient_topic_and_context_from_spore(graph, spore_id):
    response = graph.execute_query(
        """
        MATCH (spore:Spore)-[:SOUGHT]->(nutrient:Nutrient)-[:DESCRIBED_BY]->(context)
        WHERE elementId(spore) = $spore_id
        RETURN nutrient.topic, context.content
        """,
        spore_id=spore_id)
    record = response.records[0]
    return record[0], record[1]


def create_initial_region(graph, spore_id, inquiry):
    graph.execute_query(
        """
        MATCH (spore:Spore)
        WHERE elementId(spore) = $spore_id
        CREATE (region:Region)
        CREATE (spore)-[:SPREAD]->(region)
        CREATE (region)-[:INQUIRED]->(inquiry:Inquiry {content: $inquiry})
        """,
        spore_id=spore_id,
        inquiry=inquiry)


def create_region(graph, source_region_id, source_claim_id, inquiry):
    graph.execute_query(
        """
        MATCH (source_region:Region)
        WHERE elementId(source_region) = $source_region_id
        MATCH (source_claim:Claim)
        WHERE elementId(source_claim) = $source_claim_id
        CREATE (region:Region)
        CREATE (source_region)-[:SPREAD]->(region)
        CREATE (source_claim)-[:INFORMED]->(region)
        CREATE (region)-[:INQUIRED]->(inquiry:Inquiry {content: $inquiry})
        """,
        source_region_id=source_region_id,
        source_claim_id=source_claim_id,
        inquiry=inquiry)


def query_inquiry_without_finding(graph):
    response = graph.execute_query(
        """
        MATCH (region:Region)-[:INQUIRED]->(inquiry:Inquiry)
        WHERE NOT (region)-[:FOUND]->(:Finding)
            AND region.engagement IS NULL
        RETURN elementId(region), inquiry.content
        """)
    if len(response.records) == 0:
        return None, None
    record = response.records[0]
    return record[0], record[1]


def create_finding(graph, region_id, reasoning, content, citations):
    graph.execute_query(
        """
        MATCH (region:Region)
        WHERE elementId(region) = $region_id
        CREATE (region)-[:FOUND]->(finding:Finding {reasoning: $reasoning, content: $content, citations: $citations})
        """,
        region_id=region_id,
        reasoning=reasoning,
        content=content,
        citations=citations)


def query_finding_without_claims(graph):
    response = graph.execute_query(
        """
        MATCH (region:Region)-[:FOUND]->(finding:Finding)
        WHERE NOT (region)-[:CLAIMED]->(:Claim)
            AND region.engagement IS NULL
        RETURN elementId(region), finding.content, finding.citations
        """)
    if len(response.records) == 0:
        return None, None, None
    record = response.records[0]
    return record[0], record[1], record[2]


def create_claim(graph, region_id, content, citations):
    graph.execute_query(
        """
        MATCH (region:Region)
        WHERE elementId(region) = $region_id
        CREATE (region)-[:CLAIMED]->(claim:Claim {content: $content, citations: $citations})
        """,
        region_id=region_id,
        content=content,
        citations=citations)


def query_claim_without_relevance_or_terminus(graph):
    response = graph.execute_query(
        """
        MATCH (claim:Claim)
        WHERE NOT (claim)-[:TERMINATES]->(:Terminus)
            AND NOT (claim)-[:RELEVANT_TO]->(:Nutrient)
            AND claim.engagement IS NULL
        RETURN elementId(claim), claim.content
        """)
    if len(response.records) == 0:
        return None, None
    record = response.records[0]
    return record[0], record[1]


def bind_claim_to_nutrient(graph, claim_id, nutrient_id):
    graph.execute_query(
        """
        MATCH (claim:Claim), (nutrient:Nutrient)
        WHERE elementId(claim) = $claim_id
            AND elementId(nutrient) = $nutrient_id
        CREATE (claim)-[:RELEVANT_TO]->(nutrient)
        """,
        claim_id=claim_id,
        nutrient_id=nutrient_id)


def create_terminus(graph, claim_id):
    graph.execute_query(
        """
        MATCH (claim:Claim)
        WHERE elementId(claim) = $claim_id
        CREATE (claim)-[:TERMINATES]->(terminus:Terminus)
        """,
        claim_id=claim_id)


def query_relevant_claim_without_region(graph):
    response = graph.execute_query(
        """
        MATCH (claim:Claim)<-[:CLAIMED]-(region:Region)
        WHERE (claim)-[:RELEVANT_TO]->(:Nutrient)
            AND NOT (claim)-[:INFORMED]->(:Region)
            AND claim.engagement IS NULL
        RETURN elementId(claim), claim.content, elementId(region)
        """)
    if len(response.records) == 0:
        return None, None, None
    record = response.records[0]
    return record[0], record[1], record[2]


def query_nutrient_topic_and_context_from_claim(graph, claim_id):
    response = graph.execute_query(
        """
        MATCH (claim:Claim)-[:RELEVANT_TO]->(nutrient:Nutrient)-[:DESCRIBED_BY]->(context)
        WHERE elementId(claim) = $claim_id
        RETURN nutrient.topic, context.content
        """,
        claim_id=claim_id)
    record = response.records[0]
    return record[0], record[1]
