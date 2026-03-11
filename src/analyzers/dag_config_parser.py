from __future__ import annotations

from pathlib import Path
from typing import Any


class DAGConfigParser:
	"""Parse YAML configuration files for dbt and Airflow-style data nodes."""

	def parse_file(self, file_path: str) -> list[dict[str, Any]]:
		"""Parse a YAML file and return configuration-derived data nodes."""
		try:
			raw_text = Path(file_path).read_text(encoding="utf-8")
		except OSError:
			return []

		return self.parse_text(raw_text)

	def parse_text(self, yaml_text: str) -> list[dict[str, Any]]:
		"""Parse YAML text and extract dbt and Airflow configuration nodes."""
		config = self._load_yaml(yaml_text)
		if not isinstance(config, dict):
			return []

		nodes: list[dict[str, Any]] = []
		nodes.extend(self._extract_dbt_sources(config))
		nodes.extend(self._extract_dbt_models(config))
		nodes.extend(self._extract_airflow_dags(config))
		return nodes

	def _load_yaml(self, yaml_text: str) -> Any:
		try:
			import yaml
		except ImportError:
			return None

		try:
			return yaml.safe_load(yaml_text)
		except Exception:
			return None

	def _extract_dbt_sources(self, config: dict[str, Any]) -> list[dict[str, Any]]:
		sources_block = config.get("sources")
		if not isinstance(sources_block, list):
			return []

		source_nodes: list[dict[str, Any]] = []
		for entry in sources_block:
			if not isinstance(entry, dict):
				continue

			name = entry.get("name")
			if not name:
				continue

			source_nodes.append(
				{
					"node_type": "dbt_source",
					"name": str(name),
					"database": self._value_or_none(entry.get("database")),
					"schema": self._value_or_none(entry.get("schema")),
				}
			)

		return source_nodes

	def _extract_dbt_models(self, config: dict[str, Any]) -> list[dict[str, Any]]:
		models_block = config.get("models")
		if models_block is None:
			return []

		model_nodes: list[dict[str, Any]] = []
		self._walk_models(models_block, model_nodes)
		return model_nodes

	def _walk_models(self, node: Any, model_nodes: list[dict[str, Any]]) -> None:
		if isinstance(node, list):
			for item in node:
				self._walk_models(item, model_nodes)
			return

		if not isinstance(node, dict):
			return

		# dbt schema-style model entries commonly include `name` and optional db/schema.
		if "name" in node:
			model_nodes.append(
				{
					"node_type": "dbt_model",
					"name": str(node.get("name")),
					"database": self._value_or_none(node.get("database") or node.get("+database")),
					"schema": self._value_or_none(node.get("schema") or node.get("+schema")),
				}
			)

		for value in node.values():
			if isinstance(value, (dict, list)):
				self._walk_models(value, model_nodes)

	def _extract_airflow_dags(self, config: dict[str, Any]) -> list[dict[str, Any]]:
		dag_nodes: list[dict[str, Any]] = []
		self._walk_for_airflow_dags(config, dag_nodes, parent_key=None)
		return dag_nodes

	def _walk_for_airflow_dags(
		self,
		node: Any,
		dag_nodes: list[dict[str, Any]],
		parent_key: str | None,
	) -> None:
		if isinstance(node, list):
			for item in node:
				self._walk_for_airflow_dags(item, dag_nodes, parent_key=parent_key)
			return

		if not isinstance(node, dict):
			return

		has_airflow_markers = "schedule_interval" in node or "default_args" in node
		if has_airflow_markers:
			dag_id = node.get("dag_id") or node.get("id") or parent_key or "unknown_dag"
			dag_nodes.append(
				{
					"node_type": "airflow_dag",
					"dag_id": str(dag_id),
					"schedule_interval": self._value_or_none(node.get("schedule_interval")),
				}
			)

		for key, value in node.items():
			if isinstance(value, (dict, list)):
				self._walk_for_airflow_dags(value, dag_nodes, parent_key=str(key))

	def _value_or_none(self, value: Any) -> str | None:
		if value is None:
			return None
		return str(value)
