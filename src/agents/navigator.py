from __future__ import annotations

from difflib import get_close_matches
import json
import os
import re
from pathlib import Path
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from openai import OpenAI
from pydantic import BaseModel
from typing_extensions import TypedDict


class NavigatorState(TypedDict, total=False):
	question: str
	target_entity: str
	query_type: str
	history: list[str]
	evidence: list[str]
	tool_name: str
	tool_input: str
	response: str


class ParsedNavigatorQuery(BaseModel):
	"""Structured parse of a navigator user query."""
	target_entity: str
	query_type: Literal["lineage", "implementation"]


class NavigatorAgent:
	"""Question-answering navigator over cartography artifacts using LangGraph."""

	def __init__(self, project_name: str = "workspace", cartography_dir: str = ".cartography") -> None:
		self.project_name = project_name
		self.cartography_dir = cartography_dir
		self.project_dir = Path(cartography_dir) / project_name
		self._history: list[str] = []
		self._evidence: list[str] = []
		self._model_name = "google/gemini-2.0-flash-001"
		self._client = None

		api_key = os.getenv("OPENROUTER_API_KEY")
		if api_key:
			self._client = OpenAI(
				base_url="https://openrouter.ai/api/v1",
				api_key=api_key,
			)

		builder = StateGraph(NavigatorState)
		builder.add_node("parse_query", self._parse_query)
		builder.add_node("route_question", self._route_question)
		builder.add_node("run_tool", self._run_tool)
		builder.add_edge(START, "parse_query")
		builder.add_edge("parse_query", "route_question")
		builder.add_edge("route_question", "run_tool")
		builder.add_edge("run_tool", END)
		self.graph = builder.compile()

	def _parse_query(self, state: NavigatorState) -> dict[str, str]:
		"""Use an LLM to parse user intent into a structured query payload."""
		question = str(state.get("question", "")).strip()
		if not question:
			return {"target_entity": "", "query_type": "implementation"}

		default_payload = ParsedNavigatorQuery(
			target_entity=self._extract_subject(question),
			query_type=(
				"lineage"
				if any(token in question.lower() for token in ["lineage", "upstream", "downstream", "table", "dataset"])
				else "implementation"
			),
		)

		if not self._client:
			return default_payload.model_dump()

		prompt = (
			"You classify data-code navigation questions. "
			"Return ONLY valid JSON with keys: target_entity, query_type. "
			"query_type must be either 'lineage' or 'implementation'. "
			"target_entity should be the most relevant dataset/table/module identifier from the question.\n\n"
			f"Question: {question}"
		)

		try:
			response = self._client.chat.completions.create(
				model=self._model_name,
				messages=[
					{
						"role": "user",
						"content": prompt,
					}
				],
				temperature=0,
			)
			raw_content = response.choices[0].message.content or ""
			clean_json = raw_content.replace("```json", "").replace("```", "").strip()
			parsed = ParsedNavigatorQuery.model_validate(json.loads(clean_json))
			print(f"LLM successfully parsed query: {parsed}")
			return parsed.model_dump()
		except Exception:
			return default_payload.model_dump()

	def ask(self, question: str) -> str:
		"""Run one navigation turn against artifacts and return the tool response."""
		initial_state: NavigatorState = {
			"question": question,
			"history": list(self._history),
			"evidence": list(self._evidence),
		}
		result = self.graph.invoke(initial_state)
		self._history = result.get("history", self._history)
		self._evidence = result.get("evidence", self._evidence)
		return result.get("response", "No response generated.")

	def find_implementation(self, concept: str) -> str:
		"""Scan CODEBASE.md for lines relevant to a concept."""
		artifact = "CODEBASE.md"
		path = str(self.project_dir / artifact)
		if not os.path.exists(path):
			return (
				f"No implementation notes found because {path} does not exist.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		with open(path, "r", encoding="utf-8") as f:
			lines = f.readlines()

		needle = concept.strip().lower()
		matches = [line.strip() for line in lines if needle and needle in line.lower()]
		if not matches:
			body = f"No direct CODEBASE.md matches found for concept '{concept}'."
		else:
			body = "\n".join(f"- {line}" for line in matches[:10])

		return f"{body}\nEvidence Source: {artifact} | Analysis Method: Static"

	def trace_lineage(self, dataset_id: str) -> str:
		"""Trace direct upstream and downstream neighbors for a dataset identifier."""
		artifact = "lineage_graph.json"
		data = self._load_json_artifact(artifact)
		if not data:
			return (
				"Lineage graph is unavailable for tracing.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		nodes = data.get("nodes", [])
		edges = data.get("edges", [])
		targets = [
			str(node.get("id", ""))
			for node in nodes
			if dataset_id.lower() in str(node.get("id", "")).lower()
		]

		if not targets:
			return (
				f"No lineage nodes matched '{dataset_id}'.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		parts: list[str] = []
		for target in targets[:5]:
			upstream = sorted(
				{
					str(edge.get("source"))
					for edge in edges
					if str(edge.get("target")) == target
				}
			)
			downstream = sorted(
				{
					str(edge.get("target"))
					for edge in edges
					if str(edge.get("source")) == target
				}
			)
			parts.append(
				f"Dataset: {target}\n"
				f"- Upstream: {', '.join(upstream) if upstream else 'None'}\n"
				f"- Downstream: {', '.join(downstream) if downstream else 'None'}"
			)

		return "\n\n".join(parts) + f"\nEvidence Source: {artifact} | Analysis Method: Static"

	def blast_radius(self, module_id: str) -> str:
		"""Find modules that depend on the target module (incoming dependency edges)."""
		artifact = "module_graph.json"
		data = self._load_json_artifact(artifact)
		if not data:
			return (
				"Module graph is unavailable for blast radius analysis.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		nodes = data.get("nodes", [])
		edges = data.get("edges", [])

		candidate_ids = [str(node.get("id", "")) for node in nodes]
		target_id = self._resolve_identifier(module_id, candidate_ids)
		if not target_id:
			return (
				f"Could not resolve module '{module_id}' in module graph.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		dependents = sorted(
			{
				str(edge.get("source"))
				for edge in edges
				if str(edge.get("target")) == target_id
				and str(edge.get("relation", "")).upper() == "DEPENDS_ON"
			}
		)

		if not dependents:
			body = f"No direct DEPENDS_ON dependents found for {target_id}."
		else:
			body = "\n".join(f"- {item}" for item in dependents)
			body = f"Modules impacted by changes to {target_id}:\n{body}"

		return f"{body}\nEvidence Source: {artifact} | Analysis Method: Static"

	def explain_module(self, file_path: str) -> str:
		"""Return semantic_analysis for a specific module path from module graph."""
		artifact = "module_graph.json"
		data = self._load_json_artifact(artifact)
		if not data:
			return (
				"Module graph is unavailable for module explanation.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		nodes = data.get("nodes", [])
		candidate_ids = [str(node.get("id", "")) for node in nodes]
		resolved = self._resolve_identifier(file_path, candidate_ids)
		if not resolved:
			return (
				f"Module '{file_path}' was not found in module graph.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		for node in nodes:
			if str(node.get("id", "")) != resolved:
				continue
			semantic = node.get("semantic_analysis")
			if isinstance(semantic, dict):
				formatted = json.dumps(semantic, indent=2)
				return (
					f"Semantic analysis for {resolved}:\n{formatted}\n"
					f"Evidence Source: {artifact} | Analysis Method: Static"
				)
			return (
				f"No semantic_analysis found for {resolved}.\n"
				f"Evidence Source: {artifact} | Analysis Method: Static"
			)

		return (
			f"Module '{file_path}' lookup failed unexpectedly.\n"
			f"Evidence Source: {artifact} | Analysis Method: Static"
		)

	def _route_question(self, state: NavigatorState) -> dict[str, str]:
		"""Decide which tool to run from user question intent."""
		question = str(state.get("question", "")).strip()
		lower = question.lower()
		target_entity = str(state.get("target_entity", "")).strip()
		query_type = str(state.get("query_type", "implementation")).strip().lower()

		tool_subject = target_entity if target_entity else self._extract_subject(question)

		if any(token in lower for token in ["lineage", "upstream", "downstream", "table", "dataset"]):
			tool_name = "trace_lineage"
			tool_input = tool_subject
		elif any(token in lower for token in ["blast radius", "impact", "if i change", "dependency"]):
			tool_name = "blast_radius"
			tool_input = tool_subject
		elif any(token in lower for token in ["explain", "what does", "purpose", "module"]):
			tool_name = "explain_module"
			tool_input = tool_subject
		elif query_type == "lineage":
			tool_name = "trace_lineage"
			tool_input = tool_subject
		else:
			tool_name = "find_implementation"
			tool_input = tool_subject

		return {"tool_name": tool_name, "tool_input": tool_input}

	def _run_tool(self, state: NavigatorState) -> NavigatorState:
		"""Execute selected tool and update conversation/evidence history."""
		tool_name = str(state.get("tool_name", "find_implementation"))
		tool_input = str(state.get("tool_input", "")).strip()
		question = str(state.get("question", "")).strip()

		tools = {
			"find_implementation": self.find_implementation,
			"trace_lineage": self.trace_lineage,
			"blast_radius": self.blast_radius,
			"explain_module": self.explain_module,
		}
		tool_fn = tools.get(tool_name, self.find_implementation)
		response = tool_fn(tool_input)

		history = list(state.get("history", []))
		history.append(f"Q: {question}")
		history.append(f"A[{tool_name}]: {response}")

		evidence = list(state.get("evidence", []))
		evidence_match = re.search(r"Evidence Source:.*$", response, flags=re.MULTILINE)
		if evidence_match:
			evidence.append(evidence_match.group(0))

		return {"response": response, "history": history, "evidence": evidence}

	def _load_json_artifact(self, artifact_name: str) -> dict[str, Any]:
		if not self.project_dir.exists():
			raise FileNotFoundError(
				f"Project artifact folder not found: {self.project_dir}. "
				f"Run analysis for project '{self.project_name}' first."
			)

		path = str(self.project_dir / artifact_name)
		if not os.path.exists(path):
			return {}
		with open(path, "r", encoding="utf-8") as f:
			return json.load(f)

	def _resolve_identifier(self, raw_value: str, candidates: list[str]) -> str | None:
		def _normalize_identifier(identifier: str) -> str:
			normalized = identifier.strip()
			if normalized.lower().startswith("file:"):
				normalized = normalized[5:]
			return normalized.replace("\\", "/")

		value = _normalize_identifier(raw_value)
		if not value:
			return None
		if value in candidates:
			return value

		normalized_candidates = [(_normalize_identifier(candidate), candidate) for candidate in candidates]
		for normalized_candidate, original_candidate in normalized_candidates:
			if normalized_candidate == value:
				return original_candidate

		lowered = value.lower()
		for normalized_candidate, original_candidate in normalized_candidates:
			if normalized_candidate.lower() == lowered:
				return original_candidate

		for normalized_candidate, original_candidate in normalized_candidates:
			if normalized_candidate.lower().endswith(lowered):
				return original_candidate

		for normalized_candidate, original_candidate in normalized_candidates:
			base_name = normalized_candidate.rsplit("/", 1)[-1].lower()
			if lowered in base_name:
				return original_candidate

		lowered_candidates = [normalized_candidate.lower() for normalized_candidate, _ in normalized_candidates]
		close = get_close_matches(lowered, lowered_candidates, n=1, cutoff=0.6)
		if close:
			best_lower = close[0]
			for normalized_candidate, original_candidate in normalized_candidates:
				if normalized_candidate.lower() == best_lower:
					return original_candidate

		return None

	def _extract_subject(self, question: str) -> str:
		quoted = re.findall(r"['\"]([^'\"]+)['\"]", question)
		if quoted:
			return quoted[0]

		cleaned = re.sub(r"\?$", "", question).strip()
		cleaned = re.sub(r"\s+", " ", cleaned)

		for prefix in [
			"what happens if i change",
			"what happens if i modify",
			"explain what",
			"explain module",
			"show me",
			"show me the",
			"can you show me",
			"please show me",
			"trace lineage for",
			"find implementation of",
		]:
			if cleaned.lower().startswith(prefix):
				cleaned = cleaned[len(prefix):].strip(" :-,")

		return cleaned
