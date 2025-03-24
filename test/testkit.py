import os

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


def clear_graph(graph):
    graph.execute_query(
        """
        MATCH (n)
        DETACH DELETE n
        """)


def query_node_count(graph):
    response = graph.execute_query(
        """
        MATCH (n)
        RETURN count(n)
        """)
    return response.records[0][0]
