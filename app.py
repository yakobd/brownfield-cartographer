import streamlit as st
import json
import os
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Brownfield Cartographer")

st.title("Codebase Map: Phase 3 Visualizer")

# 1. Load the data
DATA_PATH = ".cartography/lineage_graph.json"

if not os.path.exists(DATA_PATH):
    st.error(f"Could not find {DATA_PATH}. Please run the full pipeline first.")
else:
    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Fallback compatibility for older graph wrapper shapes.
    if not nodes and "graph" in data:
        nodes = data.get("graph", {}).get("nodes", [])
        edges = data.get("graph", {}).get("edges", [])

    pagerank_values = [float(node.get("pagerank", 0.0) or 0.0) for node in nodes]
    min_rank = min(pagerank_values) if pagerank_values else 0.0
    max_rank = max(pagerank_values) if pagerank_values else 1.0

    slider_max_rank = max_rank if pagerank_values else 0.0
    if slider_max_rank > 0.0:
        min_pagerank_threshold = st.sidebar.slider(
            "Minimum PageRank Threshold",
            min_value=0.0,
            max_value=float(slider_max_rank),
            value=0.0,
        )
    else:
        min_pagerank_threshold = 0.0
        st.sidebar.slider(
            "Minimum PageRank Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            disabled=True,
        )

    filtered_nodes = [
        node for node in nodes
        if float(node.get("pagerank", 0.0) or 0.0) >= min_pagerank_threshold
    ]
    included_node_ids = {str(node.get("id", "")) for node in filtered_nodes}
    filtered_edges = [
        edge for edge in edges
        if str(edge.get("source", "")) in included_node_ids and str(edge.get("target", "")) in included_node_ids
    ]

    def node_size_from_rank(rank: float) -> float:
        if max_rank == min_rank:
            return 20.0
        normalized = (rank - min_rank) / (max_rank - min_rank)
        return 12.0 + (normalized * 28.0)

    domain_palette = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
    ]
    domain_color_map = {}

    def color_for_domain(domain: str) -> str:
        if domain not in domain_color_map:
            domain_color_map[domain] = domain_palette[len(domain_color_map) % len(domain_palette)]
        return domain_color_map[domain]

    # 2. Sidebar Stats
    st.sidebar.header("Network Stats")
    st.sidebar.metric("Total Nodes", len(filtered_nodes))
    st.sidebar.metric("Total Edges", len(filtered_edges))

    st.sidebar.subheader("Top PageRank Nodes")
    top_nodes = sorted(filtered_nodes, key=lambda x: float(x.get("pagerank", 0.0) or 0.0), reverse=True)[:3]
    for node in top_nodes:
        node_id = str(node.get("id", "unknown"))
        st.sidebar.write(f"- {os.path.basename(node_id)}")

    # 3. Create Pyvis Network
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)

    # Add Nodes
    for node in filtered_nodes:
        node_id = str(node.get("id", "unknown"))
        file_name = os.path.basename(node_id)
        pagerank = float(node.get("pagerank", 0.0) or 0.0)
        domain = str(node.get("domain", "Unknown"))

        semantic = node.get("semantic_analysis") if isinstance(node.get("semantic_analysis"), dict) else {}
        purpose = semantic.get("purpose") if isinstance(semantic.get("purpose"), str) else ""

        tooltip = f"{node_id}<br>Domain: {domain}<br>PageRank: {pagerank:.6f}"
        if purpose:
            tooltip += f"<br><br>Purpose: {purpose}"

        net.add_node(
            node_id,
            label=file_name,
            title=tooltip,
            color=color_for_domain(domain),
            size=node_size_from_rank(pagerank),
        )

    # Add Edges
    for edge in filtered_edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target:
            net.add_edge(source, target)

    # 4. Physics & Styling
    net.force_atlas_2based()
    
    # Save and display
    net.save_graph("map.html")
    HtmlFile = open("map.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read() 
    components.html(source_code, height=650)

    st.info("Node size is scaled by PageRank. Node color represents domain. Hover a node to see semantic purpose when available.")