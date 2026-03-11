import sqlglot
from sqlglot import exp


class SQLLineageAnalyzer:
    """Parse SQL and extract table lineage (sources and sinks)."""

    DIALECT_FALLBACKS = ["postgres", "bigquery", "snowflake", "duckdb"]

    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def extract_lineage(self, sql_code: str, dialect: str | None = None) -> dict[str, list[str]]:
        """Extract table sources/sinks from SQL while excluding CTE names from sources."""
        expression = self._parse_with_fallback(sql_code, dialect)
        if expression is None:
            return {"sources": [], "sinks": []}

        cte_names = {
            cte.alias_or_name
            for cte in expression.find_all(exp.CTE)
            if cte.alias_or_name
        }

        sinks: list[str] = []
        sink_name = self._extract_sink_name(expression)
        if sink_name:
            sinks.append(sink_name)

        sources: list[str] = []
        seen_sources: set[str] = set()
        for table in expression.find_all(exp.Table):
            table_name = self._table_name(table)
            if not table_name:
                continue

            # Skip CTE references and sink targets to keep sources external.
            if table_name in cte_names or table_name == sink_name:
                continue

            if table_name not in seen_sources:
                seen_sources.add(table_name)
                sources.append(table_name)

        return {"sources": sources, "sinks": sinks}

    def _parse_with_fallback(self, sql_code: str, dialect: str | None):
        dialect_candidates: list[str] = []
        if dialect:
            dialect_candidates.append(dialect)
        elif self.dialect:
            dialect_candidates.append(self.dialect)

        for fallback in self.DIALECT_FALLBACKS:
            if fallback not in dialect_candidates:
                dialect_candidates.append(fallback)

        for candidate in dialect_candidates:
            try:
                return sqlglot.parse_one(sql_code, read=candidate)
            except Exception:
                continue

        return None

    def extract_dependencies(self, sql_code: str) -> dict[str, list[str]]:
        """Backward-compatible wrapper for callers using the old method name."""
        return self.extract_lineage(sql_code=sql_code, dialect=self.dialect)

    def _extract_sink_name(self, expression: exp.Expression) -> str | None:
        """Find sink table for CREATE TABLE and INSERT INTO statements."""
        if isinstance(expression, exp.Create):
            return self._table_name(expression.this)

        if isinstance(expression, exp.Insert):
            return self._table_name(expression.this)

        return None

    def _table_name(self, table_expr: exp.Expression | None) -> str | None:
        """Return a normalized table identifier, preserving db/catalog when present."""
        if table_expr is None or not isinstance(table_expr, exp.Table):
            return None

        if getattr(table_expr, "parts", None):
            parts = [part.name for part in table_expr.parts if getattr(part, "name", None)]
            if parts:
                return ".".join(parts)

        return table_expr.name or None