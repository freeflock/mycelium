from pydantic import BaseModel

from communal.graph import create_finding
from spread.operation.framework import Operation
from spread.sonar import execute_search


class EngagementData(BaseModel):
    region_id: str
    inquiry: str


class CollectFinding(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, "collect_finding")
        self.engagement_data = None

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_inquiry_without_finding(self.graph, self.operation_name)
        if self.engagement_data is not None:
            return self.engagement_data.region_id
        else:
            return None

    async def act_on_engaged_node(self):
        reasoning, content, citations = await execute_search(self.engagement_data.inquiry)
        create_finding(self.graph, self.engagement_data.region_id, reasoning, content, citations)


def query_inquiry_without_finding(graph, operation_name):
    response = graph.execute_query(
        """
        MATCH (region:Region)-[:INQUIRED]->(inquiry:Inquiry)
        WHERE NOT (region)-[:FOUND]->(:Finding)
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(region)
        RETURN elementId(region), inquiry.content
        """,
        operation_name=operation_name)
    if len(response.records) == 0:
        return None
    record = response.records[0]
    engagement_data = EngagementData(region_id=record[0], inquiry=record[1])
    return engagement_data
