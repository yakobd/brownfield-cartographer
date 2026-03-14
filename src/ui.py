import json
import os
from typing import Any

import streamlit as st

from src.agents.navigator import NavigatorAgent
from src.orchestrator import Orchestrator
from src.utils.repo_manager import RepositoryManager

ARTIFACT_DIR = ".cartography"


def list_projects(cartography_root: str = ARTIFACT_DIR) -> list[str]:
    if not os.path.isdir(cartography_root):
        return []

    projects: list[str] = []
    for name in os.listdir(cartography_root):
        full_path = os.path.join(cartography_root, name)
        if os.path.isdir(full_path):
            projects.append(name)
    return sorted(projects)


def get_project_artifact_paths(project_name: str) -> dict[str, str]:
    project_dir = os.path.join(ARTIFACT_DIR, project_name)
    return {
        "project_dir": project_dir,
        "codebase": os.path.join(project_dir, "CODEBASE.md"),
        "lineage": os.path.join(project_dir, "lineage_graph.json"),
        "trace": os.path.join(project_dir, "cartography_trace.jsonl"),
    }


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


def render_chat(project_name: str) -> None:
    st.subheader("Navigator Chat")
    st.caption("Ask architecture and lineage questions over generated artifacts.")

    if not project_name:
        st.warning("Select a project to start using Navigator.")
        return

    if (
        "navigator" not in st.session_state
        or st.session_state.get("navigator_project") != project_name
    ):
        st.session_state.navigator = NavigatorAgent(project_name=project_name)
        st.session_state.navigator_project = project_name
        st.session_state.chat_messages = []

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
            try:
                raw = st.session_state.navigator.ask(prompt)
            except FileNotFoundError as exc:
                st.warning(str(exc))
                return
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


def render_artifacts(project_name: str) -> None:
    st.subheader("Artifact Viewer")

    if not project_name:
        st.warning("Select a project to view artifacts.")
        return

    artifact_paths = get_project_artifact_paths(project_name)
    project_dir = artifact_paths["project_dir"]
    codebase_path = artifact_paths["codebase"]
    lineage_path = artifact_paths["lineage"]
    trace_path = artifact_paths["trace"]

    if not os.path.isdir(project_dir):
        st.warning(f"Project folder '{project_name}' is missing under {ARTIFACT_DIR}.")
        return

    if not any(os.scandir(project_dir)):
        st.warning(f"Project folder '{project_name}' is empty. Run analysis first.")
        return

    codebase_tab, lineage_tab, audit_tab = st.tabs(["CODEBASE.md", "Lineage Map", "Audit Log"])

    with codebase_tab:
        if not os.path.exists(codebase_path):
            st.info("Please run analysis to generate CODEBASE.md.")
        else:
            with open(codebase_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())

    with lineage_tab:
        lineage_data = load_json_file(lineage_path)
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
        entries = load_trace_entries(trace_path)
        if not entries:
            st.info("Please run analysis to generate cartography_trace.jsonl.")
        else:
            st.dataframe(entries, use_container_width=True)


def main() -> None:
    st.set_page_config(layout="wide", page_title="Brownfield Cartographer Dashboard")
    apply_dark_mode_styles()

    st.title("Brownfield Cartographer Dashboard")

    st.sidebar.header("Controls")

    projects = list_projects()
    if "selected_project" not in st.session_state:
        st.session_state.selected_project = projects[0] if projects else ""

    if projects:
        default_project = st.session_state.selected_project if st.session_state.selected_project in projects else projects[0]
        selected_project = st.sidebar.selectbox(
            "Project",
            options=projects,
            index=projects.index(default_project),
            help="Choose which project's artifacts and lineage map to load.",
        )
        st.session_state.selected_project = selected_project
    else:
        selected_project = ""
        st.session_state.selected_project = ""
        st.sidebar.selectbox(
            "Project",
            options=["(no projects found)"],
            index=0,
            disabled=True,
        )
        st.sidebar.warning("No project folders found in .cartography yet.")

    repo_target = st.sidebar.text_input(
        "Repository Target",
        value=".",
        help="Provide a local path or a GitHub repository URL.",
    )
    incremental_mode = st.sidebar.toggle("Incremental Mode", value=False)
    run_clicked = st.sidebar.button("Run Full Analysis", type="primary", use_container_width=True)

    if run_clicked:
        with st.spinner("Running cartography pipeline..."):
            analysis_path: str | None = None
            cloned_from_github = False
            try:
                analysis_path = RepositoryManager.prepare_repo(repo_target)
                cloned_from_github = RepositoryManager.is_github_url(repo_target)
                if cloned_from_github:
                    st.info("📥 Cloning remote repository...")

                orchestrator = Orchestrator(repo_path=analysis_path)
                orchestrator.run_all(incremental=incremental_mode)
                st.session_state.selected_project = orchestrator.project_name
                st.session_state.navigator = NavigatorAgent(project_name=orchestrator.project_name)
                st.session_state.navigator_project = orchestrator.project_name
                st.session_state.chat_messages = []
                st.sidebar.success(f"Analysis completed. Artifacts refreshed in {orchestrator.output_dir}.")
                st.rerun()
            except Exception as exc:
                st.sidebar.error(f"Analysis failed: {exc}")
            finally:
                if cloned_from_github and analysis_path:
                    RepositoryManager.cleanup(analysis_path)

    left_col, right_col = st.columns([1.2, 1.0])
    with left_col:
        render_chat(st.session_state.get("selected_project", ""))
    with right_col:
        render_artifacts(st.session_state.get("selected_project", ""))


if __name__ == "__main__":
    main()
