from pydantic import BaseModel
from typing import Any

class Node(BaseModel):
    '''Represents a node in a graph with associated metadata.

    Attributes:
        id (str): A unique identifier for the node. Defaults to a random UUID.
        type (str): The type or label of the node. Defaults to "Node".
        metadata (dict[str, Any]): Additional metadata associated with the node.
            Defaults to an empty dictionary.
    '''
    id: str
    type: str
    metadata: dict[str, Any]

class Edge(BaseModel):
    '''Represents a directed relationship between two nodes in a graph.

    Attributes:
        id (str): A unique identifier for the edge. Defaults to a random UUID.
        type (str): The type of the edge/relationship. Defaults to "Edge".
        source_id (str): The ID of the source node.
        target_id (str): The ID of the target node.
        metadata (dict[str, Any]): Additional metadata associated with the edge.
            Defaults to an empty dictionary.
    '''
    id: str
    type: str
    source_id: str
    target_id: str
    metadata: dict[str, Any]

class Graph(BaseModel):
    """Represents a complete graph structure with nodes and edges.

    Attributes:
        id (str): A unique identifier for the graph. Defaults to a random UUID.
        nodes (list[Node]): A list of nodes in the graph. Defaults to an empty list.
        edges (list[Edge]): A list of edges in the graph. Defaults to an empty list.
        metadata (dict[str, Any]): Additional metadata about the graph.
            Defaults to an empty dictionary.
    """
    id: str
    nodes: list[Node]
    edges: list[Edge]
    metadata: dict[str, Any]
