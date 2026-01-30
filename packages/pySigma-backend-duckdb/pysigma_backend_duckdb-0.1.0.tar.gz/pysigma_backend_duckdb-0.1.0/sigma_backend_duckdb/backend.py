"""DuckDB backend for Sigma rule validation against local JSON logs.

This module provides a pySigma-compatible backend that generates DuckDB SQL
queries for validating Sigma rules against local JSON log files in CI.

The backend extends the SQLite backend since DuckDB uses compatible SQL syntax,
with some DuckDB-specific optimizations.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from sigma.backends.sqlite import sqliteBackend
from sigma.collection import SigmaCollection
from sigma.conversion.state import ConversionState
from sigma.correlations import SigmaCorrelationRule
from sigma.processing.pipeline import ProcessingPipeline
from sigma.rule import SigmaRule

from .pipelines import splunk_sysmon

if TYPE_CHECKING:
    from pathlib import Path

    from .log_index import LogIndex, ValidationResult


class DuckDBBackend(sqliteBackend):
    """DuckDB-compatible backend for Sigma rule validation.

    Extends the SQLite backend with DuckDB-specific features:
    - Dot notation for nested fields (process.command_line)
    - ILIKE for case-insensitive matching
    - regexp_matches() function for regex
    """

    name = "DuckDB backend for local validation"

    # Override field quoting for DuckDB - use double quotes for fields with dots
    field_quote = '"'
    field_quote_pattern = re.compile(r"^[\w.]+$")

    # DuckDB uses ILIKE for case-insensitive LIKE
    # No ESCAPE clause needed - backslashes are literal in DuckDB ILIKE
    contains_expression = "{field} ILIKE '%{value}%'"
    startswith_expression = "{field} ILIKE '{value}%'"
    endswith_expression = "{field} ILIKE '%{value}'"

    # Don't escape backslashes - DuckDB ILIKE treats them literally
    escape_char = None
    add_escaped = ""
    wildcard_match_str_expression = "{field} ILIKE '{value}'"

    # DuckDB regex function
    re_expression = "regexp_matches({field}, '{regex}')"

    # Table name for queries
    table = "logs"

    def __init__(
        self,
        processing_pipeline: ProcessingPipeline | None = None,
        **kwargs,
    ):
        """Initialize DuckDB backend.

        Args:
            processing_pipeline: Pipeline for field mappings.
                               Defaults to splunk_sysmon() for Sysmon field names.
        """
        if processing_pipeline is None:
            processing_pipeline = splunk_sysmon()

        super().__init__(processing_pipeline=processing_pipeline, **kwargs)

    def finalize_query_default(
        self,
        rule: SigmaRule | SigmaCorrelationRule,
        query: str,
        index: int,
        state: ConversionState,
    ) -> str:
        """Finalize query with DuckDB-compatible SQL."""
        # For correlation rules, the query is already complete
        if isinstance(rule, SigmaCorrelationRule):
            return query

        # Build the SELECT query
        return f"SELECT * FROM {self.table} WHERE {query}"

    def validate_rule(
        self,
        rule_yaml: str,
        index: "LogIndex",
        max_results: int = 100,
    ) -> "ValidationResult":
        """Validate a Sigma rule against a log index.

        Args:
            rule_yaml: The Sigma rule YAML content
            index: LogIndex containing the logs to search
            max_results: Maximum number of matched logs to return

        Returns:
            ValidationResult with match details
        """
        from .log_index import ValidationResult

        result = ValidationResult(
            rule_title="Unknown",
            rule_id=None,
            query="",
            total_logs=len(index),
            match_count=0,
        )

        # Parse the rule
        try:
            rule = SigmaRule.from_yaml(rule_yaml)
            result.rule_title = rule.title
            result.rule_id = str(rule.id) if rule.id else None
        except Exception as e:
            result.errors.append(f"Failed to parse rule: {e}")
            return result

        # Convert to SQL
        try:
            collection = SigmaCollection(init_rules=[rule])
            queries = self.convert(collection)
            if not queries:
                result.errors.append("No query generated")
                return result
            result.query = queries[0]
        except Exception as e:
            result.errors.append(f"Failed to convert rule: {e}")
            return result

        # Execute query
        try:
            con = index.get_connection()
            rows = con.execute(result.query).fetchall()
            result.match_count = len(rows)

            # Get column names for result dict
            col_names = [desc[0] for desc in con.description]

            # Convert to dicts (limit results)
            for row in rows[:max_results]:
                result.matched_logs.append(dict(zip(col_names, row)))

        except Exception as e:
            result.errors.append(f"Query execution failed: {e}")

        return result

    def validate_rule_file(
        self,
        rule_path: "Path",
        index: "LogIndex",
        max_results: int = 100,
    ) -> "ValidationResult":
        """Validate a Sigma rule file against a log index."""
        from pathlib import Path

        rule_yaml = Path(rule_path).read_text()
        return self.validate_rule(rule_yaml, index, max_results)
