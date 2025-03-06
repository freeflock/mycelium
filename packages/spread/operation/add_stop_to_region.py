from spread.operation.framework import Operation

class AddStopToRegion(Operation):
    # TODO: Add class description.
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, operation_name="add_stop_to_region")
        self.engagement_data = None
        self.max_relevant_claims = 3

    async def query_node_to_engage(self) -> str | None:
        self.engagement_data = query_region_with_fewer_than_max_relevant_claims(self.graph,
                                                                                self.operation_name,
                                                                                self.max_relevant_claims)
        if self.engagement_data is not None:
            return self.engagement_data.region_id
        else:
            return None

    async def act_on_engaged_node(self):
        return None