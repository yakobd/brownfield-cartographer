from __future__ import annotations

import logging
from typing import Dict, List


class PythonDataFlowAnalyzer:
	"""Extract source/sink data operations from a Python Tree-sitter AST."""

	DYNAMIC_REFERENCE = "dynamic_reference, cannot resolve"

	SOURCE_CALLS = {"pd.read_csv", "pd.read_sql", "pd.read_json"}
	SINK_CALLS = {"df.to_csv", "df.to_sql", "df.to_json"}

	def extract_data_operations(self, tree, code) -> Dict[str, List[str]]:
		"""Return data sources and sinks found in call nodes.

		Args:
			tree: Tree-sitter parse tree for Python code.
			code: Source code as `str` or `bytes`.

		Returns:
			dict: {"sources": [...], "sinks": [...]} where each item is the
			extracted first argument string or an unresolved dynamic marker.
		"""
		code_bytes = code if isinstance(code, bytes) else code.encode("utf-8")
		sources: List[str] = []
		sinks: List[str] = []

		for call_node in self._find_call_nodes(tree.root_node):
			callee = self._callee_name(call_node, code_bytes)
			if not callee:
				continue

			first_arg = self._first_argument(call_node)
			first_ref = self._argument_to_reference(first_arg, code_bytes)

			if callee in self.SOURCE_CALLS:
				sources.append(first_ref)
				continue

			if callee in self.SINK_CALLS:
				sinks.append(first_ref)
				continue

			if callee == "session.execute":
				op_kind = self._execute_operation_kind(first_arg, code_bytes)
				if op_kind == "source":
					sources.append(first_ref)
				elif op_kind == "sink":
					sinks.append(first_ref)

		return {"sources": sources, "sinks": sinks}

	def _find_call_nodes(self, root_node):
		stack = [root_node]
		while stack:
			node = stack.pop()
			if node.type == "call":
				yield node
			stack.extend(reversed(node.children))

	def _callee_name(self, call_node, code_bytes: bytes) -> str:
		function_node = call_node.child_by_field_name("function")
		if function_node is None:
			return ""
		return self._node_text(function_node, code_bytes)

	def _first_argument(self, call_node):
		args_node = call_node.child_by_field_name("arguments")
		if args_node is None:
			return None

		for child in args_node.named_children:
			return child
		return None

	def _execute_operation_kind(self, first_arg_node, code_bytes: bytes) -> str:
		"""Classify session.execute(<arg>) as source (select) or sink (insert)."""
		if first_arg_node is None or first_arg_node.type != "call":
			return ""

		inner_fn = first_arg_node.child_by_field_name("function")
		if inner_fn is None:
			return ""

		inner_name = self._node_text(inner_fn, code_bytes)
		if inner_name == "select" or inner_name.endswith(".select"):
			return "source"
		if inner_name == "insert" or inner_name.endswith(".insert"):
			return "sink"
		return ""

	def _argument_to_reference(self, arg_node, code_bytes: bytes) -> str:
		if arg_node is None:
			return self._dynamic_reference()

		if arg_node.type == "string":
			literal = self._node_text(arg_node, code_bytes)
			prefix = literal[:2].lower()
			if literal[:1].lower() == "f" or prefix in {"fr", "rf"}:
				return self._dynamic_reference()

			# Trim quotes for plain string literals.
			value = literal.strip()
			for quote in ("\"\"\"", "'''", "\"", "'"):
				if value.startswith(quote) and value.endswith(quote) and len(value) >= len(quote) * 2:
					return value[len(quote) : -len(quote)]
			return self._dynamic_reference()

		# Names, attributes, calls, f-strings, concatenations, etc.
		return self._dynamic_reference()

	def _dynamic_reference(self) -> str:
		logging.warning(self.DYNAMIC_REFERENCE)
		return self.DYNAMIC_REFERENCE

	def _node_text(self, node, code_bytes: bytes) -> str:
		return code_bytes[node.start_byte : node.end_byte].decode("utf-8").strip()
