from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, List, Tuple

import networkx as nx
from tree_sitter import Language, Parser, Query
import tree_sitter_sql
import tree_sitter_yaml
import tree_sitter_python as tspython

from src.analyzers.git_analyzer import get_git_velocity as git_velocity_for_file
from src.models.models import CodeEntity, FileNode, ModuleNode


class Surveyor:
    """Multi-lingual parser for Python, SQL, and YAML source mapping."""

    def __init__(self) -> None:
        # Initialize grammar objects per file extension.
        self.langs = {
            ".py": Language(tspython.language()),
            ".sql": Language(tree_sitter_sql.language()),
            ".yml": Language(tree_sitter_yaml.language()),
            ".yaml": Language(tree_sitter_yaml.language()),
        }

        self.parser = Parser()
        self.excluded_dirs = {".git", ".venv", "venv", "node_modules", "__pycache__", ".cartography"}
        self.graph = nx.DiGraph()

    def scan_repository(self, repo_path: str) -> List[FileNode]:
        """Walk a repository and return parsed FileNodes for supported files."""
        knowledge_graph: List[FileNode] = []

        for root, dirs, files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            for file_name in files:
                if not file_name.endswith((".py", ".sql", ".yml", ".yaml")):
                    continue

                full_path = os.path.join(root, file_name)
                try:
                    file_node = self.parse_file(full_path)
                    file_node.change_frequency = self.get_git_velocity(full_path)
                    knowledge_graph.append(file_node)
                except Exception:
                    # Keep scanning even if a single file cannot be parsed.
                    continue

        return knowledge_graph

    def parse_file(self, file_path: str) -> FileNode:
        path = Path(file_path)
        ext = path.suffix
        source_bytes = path.read_bytes()
        
        lang = self.langs.get(ext)
        if not lang:
            return self._create_empty_node(path, source_bytes)

        self.parser.language = lang
        tree = self.parser.parse(source_bytes)
        root = tree.root_node
        
        imports: List[str] = []
        entities: List[CodeEntity] = []

        # Route to specific extractors
        if ext == ".py":
            imports = self._extract_python_imports(root, source_bytes)
            entities = self._extract_python_entities(root, source_bytes)
        elif ext == ".sql":
            imports = self._extract_sql_deps(source_bytes)
        elif ext in [".yml", ".yaml"]:
            imports = self._extract_yaml_deps(source_bytes)

        return FileNode(
            file_path=str(path),
            language=ext[1:] if ext else "unknown",
            file_size=len(source_bytes),
            imports=imports,
            entities=entities,
            change_frequency=0,
        )

    def get_git_velocity(self, file_path: str) -> int:
        """Return commit-frequency signal for a file."""
        return git_velocity_for_file(file_path)

    def to_module_nodes(self, nodes: List[FileNode]) -> List[ModuleNode]:
        """Convert FileNode objects into typed ModuleNode objects."""
        module_nodes: List[ModuleNode] = []
        for node in nodes:
            module_nodes.append(
                ModuleNode(
                    id=node.file_path,
                    file_path=node.file_path,
                    language=node.language,
                    file_size=node.file_size,
                    imports=node.imports,
                    change_frequency=node.change_frequency,
                )
            )
        return module_nodes

    def build_graph(self, nodes: List[ModuleNode]) -> nx.DiGraph:
        """Build a directed dependency graph from module nodes."""
        self.graph = nx.DiGraph()

        lookup = self._build_module_lookup(nodes)
        for node in nodes:
            self.graph.add_node(
                node.id,
                type=node.type,
                file_path=node.file_path,
                language=node.language,
                file_size=node.file_size,
                change_frequency=node.change_frequency,
            )

        for node in nodes:
            for import_name in node.imports:
                target_id = self._resolve_import_target(import_name, lookup)
                if target_id and target_id in self.graph:
                    self.graph.add_edge(node.id, target_id, relation="DEPENDS_ON")

        return self.graph

    def calculate_pagerank(self, top_n: int = 5) -> List[Tuple[str, float]]:
        """Calculate PageRank scores and return top architectural hubs."""
        if self.graph.number_of_nodes() == 0:
            return []
        pagerank = nx.pagerank(self.graph)
        return sorted(pagerank.items(), key=lambda item: item[1], reverse=True)[:top_n]

    def detect_dead_code(self) -> List[str]:
        """Return modules with zero in-degree (not imported by others)."""
        if self.graph.number_of_nodes() == 0:
            return []
        return sorted([node for node in self.graph.nodes if self.graph.in_degree(node) == 0])

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies in the module graph."""
        if self.graph.number_of_nodes() == 0:
            return []
        return [cycle for cycle in nx.simple_cycles(self.graph)]

    # --- PYTHON EXTRACTORS (Restored from your original code) ---

    def _extract_python_imports(self, root, source_bytes) -> List[str]:
        query_text = "(import_statement) @import (import_from_statement) @import_from"
        nodes = self._run_query(self.langs[".py"], query_text, root)
        
        imports = []
        seen = set()
        for node, _ in nodes:
            for mod in self._extract_import_modules(node, source_bytes):
                if mod and mod not in seen:
                    seen.add(mod)
                    imports.append(mod)
        return imports

    def _extract_python_entities(self, root, source_bytes) -> List[CodeEntity]:
        query_text = "(function_definition) @function (class_definition) @class"
        nodes = self._run_query(self.langs[".py"], query_text, root)
        
        entities = []
        for node, capture in nodes:
            name_node = node.child_by_field_name("name")
            if not name_node:
                continue
            
            raw_name = source_bytes[name_node.start_byte:name_node.end_byte].decode("utf-8")
            is_private = raw_name.startswith("_")
            normalized_name = raw_name.lstrip("_") if is_private else raw_name

            if not normalized_name:
                continue

            entities.append(CodeEntity(
                name=normalized_name,
                type=capture,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
            ))
        return entities

    # --- SQL & YAML EXTRACTORS ---

    def _extract_sql_deps(self, source_bytes) -> List[str]:
        code = source_bytes.decode("utf-8")
        # Extract dbt refs: {{ ref('model_name') }}
        return list(set(re.findall(r"\{\{\s*ref\s*\(\s*['\"]([^'\"]+)['\"]\s*\)\s*\}\}", code)))

    def _extract_yaml_deps(self, source_bytes) -> List[str]:
        code = source_bytes.decode("utf-8")
        # Extract dbt sources or direct dependencies listed in YAML
        return list(set(re.findall(r"-\s*ref\s*:\s*['\"]([^'\"]+)['\"]", code)))

    # --- UTILS (The "Engine" parts) ---
    def _run_query(self, lang, query_text, root_node):
        """Run a query compatible with tree-sitter 0.25.x."""
        from tree_sitter import Query, QueryCursor
        
        # 1. Create the query first
        query = Query(lang, query_text)
        
        # 2. Create the cursor AND pass the query into it immediately
        cursor = QueryCursor(query)
        
        # 3. Execute the captures on the root node
        captures_dict = cursor.captures(root_node)
        
        # 4. Transform to the (node, capture_name) format
        results = []
        for capture_name, nodes in captures_dict.items():
            for node in nodes:
                results.append((node, capture_name))
                
        return results

    def _extract_import_modules(self, import_node, source_bytes) -> List[str]:
        modules = []
        for field in ("name", "path"):
            child = import_node.child_by_field_name(field)
            if child:
                modules.extend(self._collect_module_names(child, source_bytes))
        return modules

    def _collect_module_names(self, node, source_bytes) -> List[str]:
        if node.type in {"identifier", "dotted_name", "relative_import"}:
            name = source_bytes[node.start_byte:node.end_byte].decode("utf-8").strip()
            return [name.split(" as ", 1)[0].strip()]
        
        resolved = []
        for child in node.named_children:
            resolved.extend(self._collect_module_names(child, source_bytes))
        return resolved

    def _create_empty_node(self, path, source) -> FileNode:
        return FileNode(
            file_path=str(path),
            language="unknown",
            file_size=len(source),
            imports=[],
            entities=[],
            change_frequency=0,
        )

    def _build_module_lookup(self, nodes: List[ModuleNode]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for node in nodes:
            base_name = os.path.basename(node.file_path)
            stem, _ext = os.path.splitext(base_name)
            lookup.setdefault(base_name, node.id)
            lookup.setdefault(stem, node.id)
        return lookup

    def _resolve_import_target(self, import_name: str, lookup: dict[str, str]) -> str | None:
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