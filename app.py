import streamlit as st
import json
import os
from pyvis.network import Network
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Brownfield Cartographer")

st.title("🗺️ Codebase Map: Phase 1 Visualizer")

# 1. Load the data
DATA_PATH = ".cartography/module_graph.json"

if not os.path.exists(DATA_PATH):
    st.error(f"Could not find {DATA_PATH}. Please run 'python -m src.main' first!")
else:
    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    # 2. Sidebar Stats
    st.sidebar.header("Network Stats")
    st.sidebar.metric("Total Nodes", len(data["graph"]["nodes"]))
    st.sidebar.metric("Circular Loops", len(data["circular_dependencies"]))
    
    st.sidebar.subheader("Top Architectural Hubs")
    for hub in data["hubs"][:3]:
        st.sidebar.write(f"- {os.path.basename(hub)}")

    # 3. Create Pyvis Network
    net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)

    # Add Nodes
    for node in data["graph"]["nodes"]:
        file_name = os.path.basename(node["id"])
        # Color nodes: High velocity = Red, Others = Blue
        is_high_velocity = node["id"] in data["high_velocity_core"]
        color = "#ff4b4b" if is_high_velocity else "#1f77b4"
        
        net.add_node(node["id"], label=file_name, title=node["id"], color=color, size=20)

    # Add Edges
    for edge in data["graph"]["edges"]:
        net.add_edge(edge["source"], edge["target"])

    # 4. Physics & Styling
    net.force_atlas_2based()
    
    # Save and display
    net.save_graph("map.html")
    HtmlFile = open("map.html", 'r', encoding='utf-8')
    source_code = HtmlFile.read() 
    components.html(source_code, height=650)

    st.info("💡 **Red nodes** represent the High-Velocity Core. **Blue nodes** are stable modules.")