"""Utilities for working with Tree-sitter language bindings."""


def get_python_language():
	"""Return the Tree-sitter Language object for Python.

	Raises:
		RuntimeError: If Tree-sitter or the Python grammar binding is unavailable.
	"""
	try:
		import tree_sitter
		import tree_sitter_python
	except ImportError as exc:
		raise RuntimeError(
			"Failed to import Tree-sitter Python dependencies. "
			"Install 'tree-sitter' and 'tree-sitter-python'."
		) from exc

	return tree_sitter.Language(tree_sitter_python.language())
