from __future__ import annotations

import json
import os
import math
import re
import shutil
import subprocess


from src.agents.surveyor import Surveyor
from src.agents.archivist import ArchivistAgent
from src.agents.semanticist import SemanticistAgent
from src.analyzers.git_analyzer import get_git_velocity
from src.agents.hydrologist import HydrologistAgent
from src.graph.knowledge_graph import KnowledgeGraphService, analyze_codebase_graph
from src.models.models import DatasetNode, Edge, FileNode, ModuleNode


class Orchestrator:
    """Coordinates execution of the codebase cartography pipeline."""

    def __init__(self, repo_path: str | None = None) -> None:
        self.repo_path = repo_path or os.getcwd()
        self.surveyor = Surveyor()
        self.hydrologist = HydrologistAgent()
        self.archivist = ArchivistAgent()
        self.semanticist = SemanticistAgent()
        self.excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".cartography"}
        self._prepared_repo_path: str | None = None
        self._temp_repo_path = os.path.abspath(os.path.join(".cartography", "temp_repo"))
        self._semantic_nodes: list[dict] | None = None

    def run(self) -> None:
        self.run_surveyor_phase()

    def run_all(self, incremental: bool = False) -> None:
        """Run survey and lineage phases with failure isolation."""
        self._semantic_nodes = None
        try:
            self._prepare_repo()
        except Exception as exc:
            print(f"ERROR: Failed to prepare repository: {exc}")
            return

        changed_files: list[str] | None = None
        if incremental:
            changed_files = self._get_changed_files_since_head()
            print(f"--- Performing Incremental Analysis on [{len(changed_files)}] changed files ---")

        try:
            self.run_surveyor_phase(changed_files=changed_files)
        except Exception as exc:
            print(f"ERROR: Surveyor phase failed: {exc}")

        try:
            self.run_lineage_phase()
        except Exception as exc:
            print(f"ERROR: Lineage phase failed: {exc}")

        try:
            module_graph_path = ".cartography/module_graph.json"
            if os.path.exists(module_graph_path):
                with open(module_graph_path, "r", encoding="utf-8") as file:
                    module_data = json.loads(file.read())
                nodes = module_data.get("nodes", [])
                self._semantic_nodes = self.semanticist.run_semantic_phase(nodes)
                print("--- Clustering semantic hubs into domains ---")
                self._semantic_nodes = self.semanticist.cluster_into_domains(self._semantic_nodes)
                print("--- Generating semantic artifacts in .cartography ---")
                report_path = self.semanticist.generate_fde_report(self._semantic_nodes)
                codebase_path = os.path.join(".cartography", "CODEBASE.md")
                if os.path.exists(codebase_path):
                    print(f"--- Codebase summary saved to {codebase_path} ---")
                else:
                    print(f"WARNING: Expected semantic artifact missing: {codebase_path}")

                if os.path.exists(report_path):
                    print(f"--- FDE report saved to {report_path} ---")
                else:
                    print(f"WARNING: Expected semantic artifact missing: {report_path}")
            else:
                print(f"WARNING: Skipping semantic phase, missing artifact: {module_graph_path}")
        except Exception as exc:
            print(f"ERROR: Semanticist phase failed: {exc}")

        try:
            self.run_archivist_phase(nodes=self._semantic_nodes)
        except Exception as exc:
            print(f"ERROR: Archivist phase failed: {exc}")
        finally:
            self._cleanup_prepared_repo()

    def run_surveyor_phase(self, changed_files: list[str] | None = None) -> None:
        """Run Surveyor parsing and save Phase 1 graph artifacts."""
        active_repo_path, local_cleanup = self._enter_repo_context()
        print(f"--- Mapping Codebase: {active_repo_path} ---")
        if not os.path.exists(active_repo_path):
            print(f"ERROR: Directory NOT FOUND at {active_repo_path}")
            if local_cleanup:
                self._cleanup_prepared_repo()
            return

        knowledge_graph: list[FileNode] = []
        removed_files: set[str] = set()
        file_count = 0

        module_graph_path = ".cartography/module_graph.json"

        if changed_files is not None:
            target_files: list[str] = []
            for changed in changed_files:
                changed_path = changed
                if not os.path.isabs(changed_path):
                    changed_path = os.path.join(active_repo_path, changed_path)
                normalized = os.path.abspath(changed_path)
                if normalized.endswith((".py", ".sql", ".yml", ".yaml")):
                    target_files.append(normalized)

            for full_path in target_files:
                file_name = os.path.basename(full_path)
                if not os.path.exists(full_path):
                    removed_files.add(full_path)
                    continue

                file_count += 1
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
        else:
            for root, dirs, files in os.walk(active_repo_path):
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

        if changed_files is not None and os.path.exists(module_graph_path):
            with open(module_graph_path, "r", encoding="utf-8") as existing_file:
                existing_data = json.loads(existing_file.read())
            existing_nodes = existing_data.get("nodes", [])
            merged_node_map = {
                str(node.get("id")): dict(node)
                for node in existing_nodes
                if isinstance(node, dict) and node.get("id")
            }

            for removed in removed_files:
                merged_node_map.pop(removed, None)

            for node in self.surveyor.to_module_nodes(knowledge_graph):
                merged_node_map[node.id] = node.model_dump()

            module_nodes = []
            for raw_node in merged_node_map.values():
                try:
                    module_nodes.append(ModuleNode.model_validate(raw_node))
                except Exception:
                    continue
        else:
            module_nodes = self.surveyor.to_module_nodes(knowledge_graph)

        self.surveyor.build_graph(module_nodes)
        surveyor_hubs = self.surveyor.calculate_pagerank()
        dead_modules = self.surveyor.detect_dead_code()
        circular_dependencies = self.surveyor.detect_cycles()

        survey_data = [
            {
                "file_path": node.file_path,
                "file_size": node.file_size,
                "imports": node.imports,
                "change_frequency": node.change_frequency,
            }
            for node in module_nodes
        ]
        module_graph_service = KnowledgeGraphService()

        for node in module_nodes:
            module_graph_service.add_typed_node(
                ModuleNode(
                    id=node.id,
                    file_path=node.file_path,
                    language=node.language,
                    file_size=node.file_size,
                    imports=node.imports,
                    change_frequency=node.change_frequency,
                )
            )

        module_lookup = self._build_module_lookup(module_nodes)
        for node in module_nodes:
            for import_name in node.imports:
                target_id = self._resolve_module_target(import_name, module_lookup)
                if target_id and target_id in module_graph_service.graph:
                    module_graph_service.add_typed_edge(
                        node.id,
                        target_id,
                        Edge(source=node.id, target=target_id, relation="DEPENDS_ON"),
                    )

        print("\n--- Running Phase 1 Analytics (NetworkX) ---")
        os.makedirs(".cartography", exist_ok=True)

        analysis = analyze_codebase_graph(module_graph_path, survey_data=survey_data)

        sorted_nodes = sorted(module_nodes, key=lambda node: node.change_frequency, reverse=True)
        if sorted_nodes:
            top_count = max(1, math.ceil(len(sorted_nodes) * 0.2))
            analysis["high_velocity_core"] = [node.id for node in sorted_nodes[:top_count]]
        else:
            analysis["high_velocity_core"] = []

        with open(module_graph_path, "w", encoding="utf-8") as file:
            file.write(module_graph_service.to_json())

        print(f"--- Done! Saved typed module graph to {module_graph_path} ---")
        print(f"--- Analytics computed for {len(analysis.get('hubs', []))} hubs ---")
        print(f"Top Architectural Hub: {analysis['hubs'][0] if analysis['hubs'] else 'N/A'}")
        print(f"Circular Loops Found: {len(analysis['circular_dependencies'])}")
        print(f"High-Velocity Core Files: {len(analysis['high_velocity_core'])}")

        print("--- Surveyor Graph Insights ---")
        if surveyor_hubs:
            formatted_hubs = [f"{node} ({score:.4f})" for node, score in surveyor_hubs]
            print(f"PageRank Hubs: {formatted_hubs}")
        else:
            print("PageRank Hubs: []")
        print(f"Dead-Code Candidates (In-degree=0): {dead_modules}")
        print(f"Circular Dependencies Detected: {circular_dependencies}")
        print("--- Phase 1 Complete ---")

        if local_cleanup:
            self._cleanup_prepared_repo()

    def _get_changed_files_since_head(self) -> list[str]:
        """Return changed files from latest commit diff (HEAD~1..HEAD)."""
        active_repo_path, _ = self._enter_repo_context()
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            cwd=active_repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"WARNING: Incremental diff failed; defaulting to full scan: {result.stderr.strip()}")
            return []

        changed = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return changed

    def run_lineage_phase(self) -> None:
        """Run lineage analysis and save the graph under .cartography."""
        active_repo_path, local_cleanup = self._enter_repo_context()
        graph = self.hydrologist.analyze_repo(active_repo_path)
        svc = KnowledgeGraphService()

        for node_id, attrs in graph.nodes(data=True):
            reference = attrs.get("reference")
            metadata = attrs.get("metadata") if isinstance(attrs.get("metadata"), dict) else {}

            dataset_name = str(
                reference
                or metadata.get("name")
                or metadata.get("dag_id")
                or node_id
            )

            svc.add_typed_node(
                DatasetNode(
                    id=str(node_id),
                    dataset_name=dataset_name,
                    database=metadata.get("database"),
                    schema=metadata.get("schema"),
                )
            )

        for source, target, attrs in graph.edges(data=True):
            relation = self._normalize_relation(attrs.get("relation"))
            if source in svc.graph and target in svc.graph:
                svc.add_typed_edge(
                    str(source),
                    str(target),
                    Edge(source=str(source), target=str(target), relation=relation),
                )

        os.makedirs(".cartography", exist_ok=True)
        output_path = ".cartography/lineage_graph.json"
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(svc.to_json())

        impact = self.hydrologist.get_impact_analysis()
        source_count = len(impact.get("sources", []))
        sink_count = len(impact.get("sinks", []))

        print(f"--- Lineage phase complete. Saved graph to {output_path} ---")
        print(f"Sources detected: {source_count} | Sinks detected: {sink_count}")

        if local_cleanup:
            self._cleanup_prepared_repo()

    def run_archivist_phase(self, nodes: list[dict] | None = None) -> None:
        """Generate human-readable summary docs from module and lineage artifacts."""
        module_graph_path = ".cartography/module_graph.json"
        lineage_graph_path = ".cartography/lineage_graph.json"

        if not os.path.exists(module_graph_path):
            raise FileNotFoundError(f"Missing required artifact: {module_graph_path}")
        if not os.path.exists(lineage_graph_path):
            raise FileNotFoundError(f"Missing required artifact: {lineage_graph_path}")

        with open(module_graph_path, "r", encoding="utf-8") as file:
            module_data = json.loads(file.read())
        with open(lineage_graph_path, "r", encoding="utf-8") as file:
            lineage_data = json.loads(file.read())

        if nodes is not None:
            module_data["nodes"] = nodes

        summary_path = self.archivist.generate_documents(module_data, lineage_data)
        codebase_path = self.archivist.generate_CODEBASE_md(module_graph_path, lineage_graph_path)
        print(f"--- Archivist phase complete. Generated summary at {summary_path} ---")
        print(f"--- Archivist phase complete. Generated CODEBASE at {codebase_path} ---")

    def _prepare_repo(self) -> str:
        """Prepare repository path, cloning remote URLs into .cartography/temp_repo."""
        if self._prepared_repo_path:
            return self._prepared_repo_path

        if self.repo_path.startswith("http"):
            if shutil.which("git") is None:
                raise RuntimeError(
                    "Git executable not found. Please install Git to analyze remote repositories."
                )

            os.makedirs(".cartography", exist_ok=True)
            if os.path.exists(self._temp_repo_path):
                shutil.rmtree(self._temp_repo_path)

            clone_cmd = ["git", "clone", "--depth", "1", self.repo_path, self._temp_repo_path]
            result = subprocess.run(clone_cmd, capture_output=True, text=True, check=False)
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "git clone failed")

            self._prepared_repo_path = self._temp_repo_path
            print(f"Prepared temporary clone at {self._prepared_repo_path}")
        else:
            self._prepared_repo_path = self.repo_path

        return self._prepared_repo_path

    def _cleanup_prepared_repo(self) -> None:
        """Cleanup temporary cloned repo when using URL-based repo paths."""
        if self.repo_path.startswith("http") and self._prepared_repo_path and os.path.exists(self._prepared_repo_path):
            shutil.rmtree(self._prepared_repo_path)
            print(f"Cleaned up temporary clone at {self._prepared_repo_path}")
        self._prepared_repo_path = None

    def _enter_repo_context(self) -> tuple[str, bool]:
        """Return active repo path and whether this call should cleanup after running."""
        if self._prepared_repo_path is not None:
            return self._prepared_repo_path, False
        return self._prepare_repo(), True

    def _build_module_lookup(self, nodes: list[FileNode]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for node in nodes:
            base_name = os.path.basename(node.file_path)
            stem, _ext = os.path.splitext(base_name)
            lookup.setdefault(base_name, node.file_path)
            lookup.setdefault(stem, node.file_path)
        return lookup

    def _resolve_module_target(self, import_name: str, lookup: dict[str, str]) -> str | None:
        normalized = import_name.strip().lstrip(".")
        if not normalized:
            return None
        if normalized in lookup:
            return lookup[normalized]
        parts = normalized.split(".")
        for part in reversed(parts):
            if part in lookup:
                return lookup[part]
        return None

    def _normalize_relation(self, relation: str | None) -> str:
        mapping = {
            "reads_from": "READS_FROM",
            "writes_to": "WRITES_TO",
            "defines": "DEFINES",
            "declared_in": "DECLARED_IN",
            "feeds": "FEEDS",
            "depends_on": "DEPENDS_ON",
            "calls": "CALLS",
            "contains": "CONTAINS",
        }
        if not relation:
            return "DEPENDS_ON"
        return mapping.get(str(relation).lower(), "DEPENDS_ON")
