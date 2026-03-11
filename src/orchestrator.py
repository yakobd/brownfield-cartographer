from __future__ import annotations

import json
import os
import math
import re

import networkx as nx

from src.agents.surveyor import Surveyor
from src.analyzers.git_analyzer import get_git_velocity
from src.agents.hydrologist import HydrologistAgent
from src.graph.knowledge_graph import analyze_codebase_graph
from src.models.models import FileNode


class Orchestrator:
    """Coordinates execution of the codebase cartography pipeline."""

    def __init__(self, repo_path: str | None = None) -> None:
        self.repo_path = repo_path or os.getcwd()
        self.surveyor = Surveyor()
        self.hydrologist = HydrologistAgent()
        self.excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".cartography"}

    def run(self) -> None:
        self.run_surveyor_phase()

    def run_surveyor_phase(self) -> None:
        """Run Surveyor parsing and save Phase 1 graph artifacts."""
        print(f"--- Mapping Codebase: {self.repo_path} ---")
        if not os.path.exists(self.repo_path):
            print(f"ERROR: Directory NOT FOUND at {self.repo_path}")
            return

        knowledge_graph: list[FileNode] = []
        file_count = 0

        for root, dirs, files in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]

            for file_name in files:
                if not file_name.endswith((".py", ".sql", ".yml", ".yaml")):
                    continue

                file_count += 1
                full_path = os.path.join(root, file_name)

                try:
                    if file_name.endswith(".py"):
                        file_node = self.surveyor.parse_file(full_path)
                    else:
                        with open(full_path, "r", encoding="utf-8") as file:
                            content = file.read()

                        dbt_refs = re.findall(r"ref\(['\"](\w+)['\"]\)", content)
                        file_node = FileNode(
                            file_path=full_path,
                            language="sql" if file_name.endswith(".sql") else "yaml",
                            file_size=os.path.getsize(full_path),
                            imports=dbt_refs,
                            entities=[],
                        )

                    file_node.change_frequency = get_git_velocity(full_path)
                    knowledge_graph.append(file_node)

                    print(
                        f"[{file_count}] Registered: {os.path.basename(file_node.file_path)} "
                        f"({file_node.language}) | Velocity: {file_node.change_frequency}"
                    )
                except Exception as exc:
                    print(f"FAILED to process {file_name}: {exc}")

        if file_count == 0:
            print("WARNING: No relevant files found. Check your repo_path!")

        survey_data = [node.model_dump() for node in knowledge_graph]

        print("\n--- Running Phase 1 Analytics (NetworkX) ---")
        os.makedirs(".cartography", exist_ok=True)
        module_graph_path = ".cartography/module_graph.json"

        analysis = analyze_codebase_graph(module_graph_path, survey_data=survey_data)

        sorted_nodes = sorted(knowledge_graph, key=lambda node: node.change_frequency, reverse=True)
        if sorted_nodes:
            top_count = max(1, math.ceil(len(sorted_nodes) * 0.2))
            analysis["high_velocity_core"] = [node.file_path for node in sorted_nodes[:top_count]]
        else:
            analysis["high_velocity_core"] = []

        with open(module_graph_path, "w", encoding="utf-8") as file:
            json.dump(analysis, file, indent=4)

        print(f"--- Done! Saved graph analysis to {module_graph_path} ---")
        print(f"Top Architectural Hub: {analysis['hubs'][0] if analysis['hubs'] else 'N/A'}")
        print(f"Circular Loops Found: {len(analysis['circular_dependencies'])}")
        print(f"High-Velocity Core Files: {len(analysis['high_velocity_core'])}")
        print("--- Phase 1 Complete ---")

    def run_lineage_phase(self) -> None:
        """Run lineage analysis and save the graph under .cartography."""
        graph = self.hydrologist.analyze_repo(self.repo_path)

        os.makedirs(".cartography", exist_ok=True)
        output_path = ".cartography/lineage_graph.json"
        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(nx.node_link_data(graph), file, indent=4)

        impact = self.hydrologist.get_impact_analysis()
        source_count = len(impact.get("sources", []))
        sink_count = len(impact.get("sinks", []))

        print(f"--- Lineage phase complete. Saved graph to {output_path} ---")
        print(f"Sources detected: {source_count} | Sinks detected: {sink_count}")
