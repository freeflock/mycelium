from spread.operation.framework import Operation

class AddStopToRegion(Operation):
    def __init__(self, graph, engagement_handle):
        super().__init__(graph, engagement_handle, operation_name="add_stop_to_region")
        self.engagement_data = None

    async def query_node_to_engage(self) -> str | None:
        return None

    async def act_on_engaged_node(self):
        return None