# The Brownfield Cartographer

The Brownfield Cartographer is a production-grade codebase intelligence system for rapid FDE onboarding. It transforms unfamiliar repositories into architecture-aware, queryable deliverables so engineering teams can reduce discovery time, surface risk early, and execute changes with confidence.

## Installation

Install dependencies with `uv`:

```bash
uv sync
```

## Usage

### Analyze Mode

Run the full analysis pipeline against either a local repository path or a remote GitHub URL.

Local path:

```bash
uv run python -m src.cli analyze --repo-path "C:/path/to/target-repo"
```

Remote GitHub URL:

```bash
uv run python -m src.cli analyze --repo-path "https://github.com/org/repo.git"
```

Incremental re-analysis (changed files only):

```bash
uv run python -m src.cli analyze --repo-path "C:/path/to/target-repo" --incremental
```

### Query Mode

Launch interactive Navigator mode to ask technical questions about the analyzed codebase:

```bash
uv run python -m src.cli query
```

Use Query Mode to investigate architecture hotspots, data lineage implications, and likely blast radius before implementation work.

## Architecture

The Brownfield Cartographer executes a four-stage pipeline:

1. Surveyor (AST): parses repository source files to map modules, imports, and structural signals.
2. Hydrologist (Lineage): extracts data flow relationships across SQL, Python, and YAML assets.
3. Semanticist (LLM): generates semantic purpose statements and high-level engineering context.
4. Archivist (Docs): compiles engagement-ready technical documentation and traceable summaries.

## Artifacts

Generated artifacts are written under `.cartography/`:

- `.cartography/module_graph.json`
- `.cartography/lineage_graph.json`
- `.cartography/CODEBASE.md`
- `.cartography/onboarding_brief.md`
- `.cartography/cartography_trace.jsonl`

## Engagement Value

This system is designed for professional client delivery where teams need fast onboarding, credible technical diagnostics, and decision-ready architecture artifacts without prolonged manual reconnaissance.
