import json
import os
from typing import Any

import streamlit as st

from src.agents.navigator import NavigatorAgent
from src.orchestrator import Orchestrator

ARTIFACT_DIR = ".cartography"
CODEBASE_PATH = os.path.join(ARTIFACT_DIR, "CODEBASE.md")
LINEAGE_PATH = os.path.join(ARTIFACT_DIR, "lineage_graph.json")
TRACE_PATH = os.path.join(ARTIFACT_DIR, "cartography_trace.jsonl")


def apply_dark_mode_styles() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #0f1117;
                color: #e5e7eb;
            }
            .block-container {
                padding-top: 1.2rem;
            }
            .evidence-callout {
                margin-top: 0.5rem;
                padding: 0.75rem 0.9rem;
                border-left: 4px solid #4f46e5;
                background: rgba(79, 70, 229, 0.12);
                border-radius: 0.5rem;
                font-size: 0.92rem;
                color: #c7d2fe;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def parse_response(payload: str) -> tuple[str, str | None]:
    marker = "Evidence Source:"
    idx = payload.rfind(marker)
    if idx == -1:
        return payload.strip(), None

    answer = payload[:idx].strip()
    evidence = payload[idx:].strip()
    return answer, evidence


def load_json_file(path: str) -> dict[str, Any] | None:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_trace_entries(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []

    entries: list[dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return sorted(entries, key=lambda x: str(x.get("timestamp", "")), reverse=True)


def render_chat() -> None:
    st.subheader("Navigator Chat")
    st.caption("Ask architecture and lineage questions over generated artifacts.")

    if "navigator" not in st.session_state:
        st.session_state.navigator = NavigatorAgent()
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("evidence"):
                st.markdown(
                    f"<div class='evidence-callout'>{msg['evidence']}</div>",
                    unsafe_allow_html=True,
                )

    prompt = st.chat_input("Example: What happens if I change the users table?")
    if not prompt:
        return

    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing artifacts..."):
            raw = st.session_state.navigator.ask(prompt)
        answer, evidence = parse_response(raw)
        st.markdown(answer)
        if evidence:
            st.markdown(
                f"<div class='evidence-callout'>{evidence}</div>",
                unsafe_allow_html=True,
            )

    st.session_state.chat_messages.append(
        {"role": "assistant", "content": answer, "evidence": evidence}
    )


def render_artifacts() -> None:
    st.subheader("Artifact Viewer")
    codebase_tab, lineage_tab, audit_tab = st.tabs(["CODEBASE.md", "Lineage Map", "Audit Log"])

    with codebase_tab:
        if not os.path.exists(CODEBASE_PATH):
            st.info("Please run analysis to generate CODEBASE.md.")
        else:
            with open(CODEBASE_PATH, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    with lineage_tab:
        lineage_data = load_json_file(LINEAGE_PATH)
        if not lineage_data:
            st.info("Please run analysis to generate lineage_graph.json.")
        else:
            nodes = lineage_data.get("nodes", [])
            edges = lineage_data.get("edges", [])
            st.write(f"Nodes: {len(nodes)} | Edges: {len(edges)}")
            if nodes:
                st.dataframe(nodes, use_container_width=True)
            else:
                st.caption("No lineage nodes available.")

    with audit_tab:
        entries = load_trace_entries(TRACE_PATH)
        if not entries:
            st.info("Please run analysis to generate cartography_trace.jsonl.")
        else:
            st.dataframe(entries, use_container_width=True)


def main() -> None:
    st.set_page_config(layout="wide", page_title="Brownfield Cartographer Dashboard")
    apply_dark_mode_styles()

    st.title("Brownfield Cartographer Dashboard")

    st.sidebar.header("Controls")
    incremental_mode = st.sidebar.toggle("Incremental Mode", value=False)
    run_clicked = st.sidebar.button("Run Full Analysis", type="primary", use_container_width=True)

    if run_clicked:
        with st.spinner("Running cartography pipeline..."):
            try:
                orchestrator = Orchestrator(repo_path=".")
                orchestrator.run_all(incremental=incremental_mode)
                st.sidebar.success("Analysis completed. Artifacts refreshed in .cartography.")
            except Exception as exc:
                st.sidebar.error(f"Analysis failed: {exc}")

    left_col, right_col = st.columns([1.2, 1.0])
    with left_col:
        render_chat()
    with right_col:
        render_artifacts()


if __name__ == "__main__":
    main()
