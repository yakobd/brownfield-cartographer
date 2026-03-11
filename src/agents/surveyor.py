from __future__ import annotations

import subprocess
import re
from pathlib import Path
from typing import Any, List, Tuple

from tree_sitter import Language, Parser, Query
import tree_sitter_sql
import tree_sitter_yaml
import tree_sitter_python as tspython

from src.models.models import CodeEntity, FileNode


class Surveyor:
    """Multi-lingual Parser for Python, SQL, and YAML with Git Velocity tracking."""

    def __init__(self) -> None:
        # Initialize grammar objects per file extension.
        self.langs = {
            ".py": Language(tspython.language()),
            ".sql": Language(tree_sitter_sql.language()),
            ".yml": Language(tree_sitter_yaml.language()),
            ".yaml": Language(tree_sitter_yaml.language()),
        }

        self.parser = Parser()

    def extract_git_velocity(self, file_path: str, days: int = 30) -> int:
        """Computes change frequency (Git log count)."""
        try:
            cmd = f'git rev-list --count --since="{days} days ago" HEAD -- "{file_path}"'
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
            return int(result.decode("utf-8").strip())
        except Exception:
            return 0

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

        velocity = self.extract_git_velocity(file_path)

        return FileNode(
            file_path=str(path),
            language=ext[1:] if ext else "unknown",
            file_size=len(source_bytes),
            imports=imports,
            entities=entities,
            change_frequency=velocity
        )

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