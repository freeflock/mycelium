from neo4j import GraphDatabase
from pydantic import BaseModel

from spread.operation.framework import Operation

class EngagementData(BaseModel):
    region_id: str

class AddStopToRegion(Operation):
    # TODO: Add class description.
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, operation_name="add_stop_to_region")
        self.engagement_data = None
        self.max_relevant_claims = 3

    async def query_node_to_engage(self) -> str | None:
        # TODO: Add method description.
        self.engagement_data = query_region_without_stop_node(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.region_id
        else:
            return None

    async def act_on_engaged_node(self):
        return None


def query_region_without_stop_node(graph: GraphDatabase.driver, operation_name: str):
    response = graph.execute_query(
        """
        MATCH (region:Region)
        WHERE NOT (region)-[:STOPPED_BY]->(:Stop)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(region)
        RETURN elementId(region)
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(region_id=record[0])
    return engagement_data