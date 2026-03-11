from __future__ import annotations

import os
from pathlib import Path

import networkx as nx
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

from src.analyzers.dag_config_parser import DAGConfigParser
from src.analyzers.python_data_flow import PythonDataFlowAnalyzer
from src.analyzers.sql_lineage import SQLLineageAnalyzer


class HydrologistAgent:
	"""Builds a cross-file data-flow graph and computes impact information."""

	def __init__(self) -> None:
		self.sql_lineage_analyzer = SQLLineageAnalyzer()
		self.python_data_flow_analyzer = PythonDataFlowAnalyzer()
		self.dag_config_parser = DAGConfigParser()

		self.python_language = Language(tspython.language())
		self.python_parser = Parser()
		self.python_parser.language = self.python_language

		self.graph = nx.DiGraph()

	def analyze_repo(self, repo_path: str) -> nx.DiGraph:
		"""Walk a repository and add SQL, Python, and YAML data nodes/edges."""
		self.graph = nx.DiGraph()

		for root, _dirs, files in os.walk(repo_path):
			for file_name in files:
				full_path = os.path.join(root, file_name)
				suffix = Path(file_name).suffix.lower()

				if suffix == ".sql":
					self._analyze_sql_file(full_path)
				elif suffix == ".py":
					self._analyze_python_file(full_path)
				elif suffix in {".yml", ".yaml"}:
					self._analyze_yaml_file(full_path)

		return self.graph

	def get_blast_radius(self, node_name: str) -> list[str]:
		"""Return all downstream nodes reachable from the given node."""
		if node_name not in self.graph:
			return []

		return sorted(nx.descendants(self.graph, node_name))

	def get_impact_analysis(self) -> dict[str, list[str]]:
		"""Return source-like and sink-like nodes from graph degree analysis."""
		source_nodes = sorted([n for n in self.graph.nodes if self.graph.in_degree(n) == 0])
		sink_nodes = sorted([n for n in self.graph.nodes if self.graph.out_degree(n) == 0])
		return {"sources": source_nodes, "sinks": sink_nodes}

	def _analyze_sql_file(self, file_path: str) -> None:
		try:
			sql_code = Path(file_path).read_text(encoding="utf-8")
		except OSError:
			return

		lineage = self.sql_lineage_analyzer.extract_lineage(sql_code)
		file_node = f"file:{file_path}"
		self.graph.add_node(file_node, node_type="sql_file", file_path=file_path)

		for source in lineage.get("sources", []):
			source_node = self._source_node_name(source)
			self.graph.add_node(source_node, node_type="source", reference=source)
			self.graph.add_edge(source_node, file_node, relation="reads_from")

		for sink in lineage.get("sinks", []):
			sink_node = self._sink_node_name(sink)
			self.graph.add_node(sink_node, node_type="sink", reference=sink)
			self.graph.add_edge(file_node, sink_node, relation="writes_to")

	def _analyze_python_file(self, file_path: str) -> None:
		try:
			code_bytes = Path(file_path).read_bytes()
		except OSError:
			return

		tree = self.python_parser.parse(code_bytes)
		data_flow = self.python_data_flow_analyzer.extract_data_operations(tree, code_bytes)

		file_node = f"file:{file_path}"
		self.graph.add_node(file_node, node_type="python_file", file_path=file_path)

		for source in data_flow.get("sources", []):
			source_node = self._source_node_name(source)
			self.graph.add_node(source_node, node_type="source", reference=source)
			self.graph.add_edge(source_node, file_node, relation="reads_from")

		for sink in data_flow.get("sinks", []):
			sink_node = self._sink_node_name(sink)
			self.graph.add_node(sink_node, node_type="sink", reference=sink)
			self.graph.add_edge(file_node, sink_node, relation="writes_to")

	def _analyze_yaml_file(self, file_path: str) -> None:
		config_nodes = self.dag_config_parser.parse_file(file_path)
		if not config_nodes:
			return

		file_node = f"file:{file_path}"
		self.graph.add_node(file_node, node_type="yaml_file", file_path=file_path)
		dbt_sources: list[str] = []
		dbt_models: list[str] = []

		for node in config_nodes:
			node_type = str(node.get("node_type", "config_node"))
			if node_type == "dbt_source":
				name = self._source_node_name(str(node.get("name", "unknown_source")))
				self.graph.add_node(name, node_type="dbt_source", metadata=node)
				self.graph.add_edge(name, file_node, relation="declared_in")
				dbt_sources.append(name)
			elif node_type == "dbt_model":
				name = self._sink_node_name(str(node.get("name", "unknown_model")))
				self.graph.add_node(name, node_type="dbt_model", metadata=node)
				self.graph.add_edge(file_node, name, relation="defines")
				dbt_models.append(name)
			elif node_type == "airflow_dag":
				dag_id = f"dag:{node.get('dag_id', 'unknown_dag')}"
				self.graph.add_node(dag_id, node_type="airflow_dag", metadata=node)
				self.graph.add_edge(file_node, dag_id, relation="defines")

		# Merge dbt schema-level sources/models into lineage with direct relationships.
		for source_node in dbt_sources:
			for model_node in dbt_models:
				self.graph.add_edge(source_node, model_node, relation="feeds")

	def _source_node_name(self, value: str) -> str:
		return f"source:{value}"

	def _sink_node_name(self, value: str) -> str:
		return f"sink:{value}"
