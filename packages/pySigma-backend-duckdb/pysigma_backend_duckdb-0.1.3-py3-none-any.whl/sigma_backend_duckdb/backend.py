"""DuckDB backend for Sigma rule validation against local JSON logs.

This module provides a pySigma-compatible backend that generates DuckDB SQL
queries for validating Sigma rules against local JSON log files in CI.

The backend extends the SQLite backend since DuckDB uses compatible SQL syntax,
with some DuckDB-specific optimizations.
"""

from __future__ import annotations

import re

from sigma.backends.sqlite import sqliteBackend
from sigma.conversion.state import ConversionState
from sigma.correlations import SigmaCorrelationRule
from sigma.processing.pipeline import ProcessingPipeline
from sigma.rule import SigmaRule

from .pipelines import splunk_sysmon


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
    escape_char = ""
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
