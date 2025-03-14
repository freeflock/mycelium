import os
import traceback
from abc import abstractmethod, ABC
from asyncio import sleep, TaskGroup
from typing import Type

from loguru import logger
from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI")
logger.info(f"NEO4J_URI: {NEO4J_URI}")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
logger.info(f"NEO4J_USERNAME: {NEO4J_USERNAME}")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
logger.info(f"NEO4J_PASSWORD: xxx")


class Operation(ABC):
    """Base class for a single atomic operation which engages and acts on a node in the graph"""

    def __init__(self, graph: GraphDatabase.driver, engagement_handle: str, operation_name: str):
        self.graph = graph
        self.engagement_data = None
        self.engagement_handle = engagement_handle
        self.operation_name = operation_name
        self.logging_identifier = f"{self.operation_name}[{self.engagement_handle}]"

    async def loop(self):
        while True:
            try:
                result = await self.operate()
                if result is False:
                    await sleep(3)
            except KeyboardInterrupt:
                raise
            except Exception as error:
                logger.error(f"(!) unhandled exception in operation {self.logging_identifier}: "
                             f"{error}\n{traceback.format_exc()}")

    async def operate(self):
        logger.info(f"{self.logging_identifier} querying node to engage")
        node_id_to_engage = await self.query_node_to_engage()
        if node_id_to_engage is None:
            logger.info(f"{self.logging_identifier} did not find a node to engage")
            return False

        logger.info(f"{self.logging_identifier} attempting to engage: {node_id_to_engage}")
        successfully_engaged = engage(self.graph, node_id_to_engage, self.engagement_handle, self.operation_name)
        if not successfully_engaged:
            logger.info(f"{self.logging_identifier} failed to engage: {node_id_to_engage}")
            return False

        logger.info(f"{self.logging_identifier} successfully engaged: {node_id_to_engage}")
        try:
            await self.act_on_engaged_node()
            return True
        finally:
            logger.info(f"{self.logging_identifier} disengaging: {node_id_to_engage}")
            disengage(self.graph, node_id_to_engage, self.operation_name)

    @abstractmethod
    async def query_node_to_engage(self) -> str | None:
        """
        Query the graph for a node to engage
        Returns the node id of the node to engage, or None if no node is found
        """
        raise NotImplementedError

    @abstractmethod
    async def act_on_engaged_node(self) -> None:
        """
        Perform an action on the node that was engaged
        At this point this instance of the operation has a lock on the node
        No other instance of the operation can act on the engaged node until this method returns
        Instances of other operations can still act on the engaged node
        Be careful not to interfere with data other operations may be using
        Rule of thumb: only add nodes and relationships, do not modify or delete existing nodes or relationships
        The latter must be handled very carefully to protect against race conditions
        Neo4j does not guarantee causal consistency between sessions:
        Writes made by other sessions may not be immediately visible - assume graph reads are out of date
        """
        raise NotImplementedError


def engage(graph, node_id, engagement_handle, operation_name):
    response = graph.execute_query(
        """
        MATCH (engagee)
        WHERE elementId(engagee) = $node_id
            AND NOT (:Engagement {operation: $operation_name})-[:ENGAGED]->(engagee)
        CREATE (engagement:Engagement {operation: $operation_name, 
                engagement_handle: $engagement_handle})-[:ENGAGED]->(engagee)
        RETURN TRUE
        """,
        node_id=node_id,
        operation_name=operation_name,
        engagement_handle=engagement_handle)
    if len(response.records) == 0:
        return False
    else:
        return True


def disengage(graph, node_id, operation_name):
    graph.execute_query(
        """
        MATCH (engagement:Engagement {operation: $operation_name})-[:ENGAGED]->(engagee)
        WHERE elementId(engagee) = $node_id
        DETACH DELETE engagement
        """,
        node_id=node_id,
        operation_name=operation_name)


def clear_all_engagements_of_operation_type(graph, operation_name):
    graph.execute_query(
        """
        MATCH (engagement:Engagement)
        WHERE engagement.operation = $operation_name
        DETACH DELETE engagement
        """,
        operation_name=operation_name)


class OperationGroup:
    """Coordinates multiple instances of an operation"""

    def __init__(self, instance_count: int, operation_subclass: Type, *args, **kwargs):
        self.operation_subclass = operation_subclass
        self.instance_count = instance_count
        self.args = args
        self.kwargs = kwargs

    async def begin(self):
        with GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as graph:
            operations = []
            for i in range(self.instance_count):
                engagement_handle = str(i)
                operation = self.operation_subclass(graph, engagement_handle, *self.args, **self.kwargs)
                operations.append(operation)
            clear_all_engagements_of_operation_type(graph, operations[0].operation_name)
            async with TaskGroup() as group:
                for operation in operations:
                    group.create_task(operation.loop())
