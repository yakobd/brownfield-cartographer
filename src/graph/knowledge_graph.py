import os
import json

import networkx as nx


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