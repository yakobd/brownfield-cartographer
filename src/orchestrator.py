from src.main import main as run_pipeline


class Orchestrator:
	"""Coordinates execution of the codebase cartography pipeline."""

	def run(self) -> None:
		run_pipeline()
