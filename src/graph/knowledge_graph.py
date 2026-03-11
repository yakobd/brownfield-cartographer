import os
import json
from typing import Dict, Type

import networkx as nx

from src.models.models import (
    BaseEdge,
    BaseNode,
    DatasetNode,
    Edge,
    FunctionNode,
    KnowledgeGraph,
    ModuleNode,
    Node,
    TransformationNode,
)


class KnowledgeGraphService:
    """Typed wrapper around a NetworkX DiGraph with Pydantic round-trip support."""

    NODE_TYPE_MAP: Dict[str, Type[BaseNode]] = {
        "module": ModuleNode,
        "dataset": DatasetNode,
        "function": FunctionNode,
        "transformation": TransformationNode,
    }

    def __init__(self, graph: nx.DiGraph | None = None) -> None:
        self.graph = graph or nx.DiGraph()

    def add_typed_node(self, node: BaseNode) -> None:
        """Validate and add a typed node to the internal graph."""
        if not isinstance(node, BaseNode):
            raise TypeError("node must be an instance of BaseNode")
        if not node.id:
            raise ValueError("node.id is required")

        attrs = node.model_dump()
        attrs["_node_model"] = node.__class__.__name__
        self.graph.add_node(node.id, **attrs)

    def add_typed_edge(self, source_id: str, target_id: str, edge: BaseEdge) -> None:
        """Validate and add a typed edge to the internal graph."""
        if not isinstance(edge, BaseEdge):
            raise TypeError("edge must be an instance of BaseEdge")
        if not source_id or not target_id:
            raise ValueError("source_id and target_id are required")
        if source_id != edge.source or target_id != edge.target:
            raise ValueError("source_id/target_id must match edge.source/edge.target")
        if source_id not in self.graph or target_id not in self.graph:
            raise ValueError("Both source_id and target_id must exist in graph before adding an edge")

        edge_attrs = edge.model_dump()
        edge_attrs["_edge_model"] = edge.__class__.__name__
        self.graph.add_edge(source_id, target_id, **edge_attrs)

    def to_knowledge_graph(self) -> KnowledgeGraph:
        """Convert the internal graph to typed Pydantic KnowledgeGraph."""
        nodes: list[BaseNode] = []
        for node_id, attrs in self.graph.nodes(data=True):
            payload = dict(attrs)
            payload.setdefault("id", str(node_id))
            payload.pop("_node_model", None)
            nodes.append(self._deserialize_node(payload))

        edges: list[BaseEdge] = []
        for source, target, attrs in self.graph.edges(data=True):
            payload = dict(attrs)
            payload.setdefault("source", str(source))
            payload.setdefault("target", str(target))
            payload.pop("_edge_model", None)
            edges.append(self._deserialize_edge(payload))

        return KnowledgeGraph(nodes=nodes, edges=edges)

    def to_json(self, indent: int = 4) -> str:
        """Serialize the typed graph to JSON."""
        kg = self.to_knowledge_graph()
        return kg.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, payload: str) -> "KnowledgeGraphService":
        """Deserialize JSON back into typed Pydantic objects and graph structure."""
        raw = json.loads(payload)
        service = cls()

        for node_payload in raw.get("nodes", []):
            node = service._deserialize_node(node_payload)
            service.add_typed_node(node)

        for edge_payload in raw.get("edges", []):
            edge = service._deserialize_edge(edge_payload)
            service.add_typed_edge(edge.source, edge.target, edge)

        return service

    def _deserialize_node(self, data: dict) -> BaseNode:
        node_type = data.get("type")
        model_cls = self.NODE_TYPE_MAP.get(node_type, Node)
        return model_cls.model_validate(data)

    def _deserialize_edge(self, data: dict) -> BaseEdge:
        return Edge.model_validate(data)


def _build_filename_index(file_paths):
    """Build filename-based lookup for node-to-node import edges."""
    filename_index = {}

    for file_path in file_paths:
        base_name = os.path.basename(file_path)
        stem, _ext = os.path.splitext(base_name)

        if base_name and base_name not in filename_index:
            filename_index[base_name] = file_path
        if stem and stem not in filename_index:
            filename_index[stem] = file_path

    return filename_index


def _resolve_import_target(import_name, filename_index):
    """Resolve an import string to a known file path via filename matching."""
    if not import_name:
        return None

    normalized = import_name.strip().lstrip(".")
    if not normalized:
        return None

    # Exact lookup first (covers imports already equal to a filename or stem).
    if normalized in filename_index:
        return filename_index[normalized]

    # Try each dotted segment from right to left (e.g., package.module -> module).
    parts = normalized.split(".")
    for part in reversed(parts):
        if part in filename_index:
            return filename_index[part]

    return None


def analyze_codebase_graph(json_path: str, survey_data=None):
    """
    Builds a directed graph from the surveyor output to identify hubs, 
    circular dependencies, and high-velocity files.
    """
    if survey_data is not None:
        data = survey_data
    else:
        if not os.path.exists(json_path):
            return {"hubs": [], "circular_dependencies": [], "high_velocity_core": [], "graph_data": {}}

        with open(json_path, "r") as f:
            data = json.load(f)

    # 1. Build the DiGraph
    G = nx.DiGraph()

    file_paths = [node.get("file_path") for node in data if node.get("file_path")]
    filename_index = _build_filename_index(file_paths)

    for node in data:
        file_path = node.get("file_path")
        if not file_path:
            continue
            
        G.add_node(file_path, size=node.get("file_size", 0), velocity=node.get("change_frequency", 0))
        
        # Create file-to-file dependency edges from import names to matched filenames.
        for imp in node.get("imports", []):
            target_file = _resolve_import_target(imp, filename_index)
            if target_file:
                G.add_edge(file_path, target_file)

    # 2. Run PageRank for Architectural Hubs
    pagerank = nx.pagerank(G) if G.number_of_nodes() > 0 else {}

    # 3. Identify Circular Dependencies (Strongly Connected Components > 1)
    scc = [list(c) for c in nx.strongly_connected_components(G) if len(c) > 1]

    # 4. Identify High-Velocity Core (Top 20%)
    sorted_by_velocity = sorted(data, key=lambda x: x.get("change_frequency", 0), reverse=True)
    top_count = max(1, int(len(data) * 0.2))
    high_velocity_core = [f["file_path"] for f in sorted_by_velocity[:top_count]]

    return {
        "hubs": [node for node, _score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]],
        "circular_dependencies": scc,
        "high_velocity_core": high_velocity_core,
        "graph_data": nx.node_link_data(G)
    }