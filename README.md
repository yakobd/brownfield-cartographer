# Brownfield Cartographer

Brownfield Cartographer is an AI-powered code reconnaissance tool designed to map legacy or unfamiliar repositories into actionable engineering insights. It combines static parsing, dependency extraction, and graph analytics to help teams quickly understand architecture, hotspots, and data flow impact before making changes.

## Project Overview

This project analyzes a target repository and produces machine-readable graph artifacts for two core perspectives:

- Module survey (code structure, imports, and velocity signals)
- Data lineage (SQL/Python/YAML-driven sources, sinks, and downstream blast radius)

The goal is to reduce onboarding and refactoring risk by making hidden codebase relationships explicit.

## Installation

This project uses `uv` for dependency management.

1. Install `uv`:

```bash
pip install uv
```

2. Sync dependencies from `pyproject.toml`/lock state:

```bash
uv sync
```

## Usage

All commands are run via the CLI entrypoint in `src/cli.py`.

### Survey

Generate the module graph and Phase 1 architecture metrics:

```bash
uv run python -m src.cli survey --repo-path <path>
```

Example:

```bash
uv run python -m src.cli survey --repo-path "C:/path/to/target-repo"
```

### Lineage

Generate the data flow lineage graph:

```bash
uv run python -m src.cli lineage --repo-path <path>
```

Example:

```bash
uv run python -m src.cli lineage --repo-path "C:/path/to/target-repo"
```

## Output Artifacts

Generated artifacts are saved under `.cartography/`:

- `.cartography/module_graph.json`
- `.cartography/lineage_graph.json`

## Technical Stack

- Python
- Tree-sitter
- SQLGlot
- NetworkX
