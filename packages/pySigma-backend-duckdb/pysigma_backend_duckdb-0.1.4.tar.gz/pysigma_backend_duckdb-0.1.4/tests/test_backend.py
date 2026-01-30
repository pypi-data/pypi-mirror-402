"""Tests for DuckDB backend."""

import pytest
from sigma.collection import SigmaCollection

from sigma_backend_duckdb import (
    DuckDBBackend,
    elastic_ecs,
    splunk_sysmon,
)

SAMPLE_RULE = """
title: Test PowerShell Encoded Command
id: a538de64-1c74-46ed-aa60-b995ed302598
status: experimental
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|contains|all:
            - powershell
            - -e
    condition: selection
"""


class TestDuckDBBackend:
    """Tests for DuckDBBackend class."""

    @pytest.fixture
    def backend(self):
        return DuckDBBackend()

    def test_query_generation(self, backend):
        """Test that correct SQL query is generated."""
        rule = SigmaCollection.from_yaml(SAMPLE_RULE)
        queries = backend.convert(rule)

        assert len(queries) == 1
        query = queries[0]

        # Check query uses Splunk Sysmon field names (identity mapping)
        assert "CommandLine" in query
        assert "SELECT * FROM logs WHERE" in query
        assert "ILIKE" in query

    def test_contains_generates_ilike(self, backend):
        """Test that contains modifier generates ILIKE."""
        rule_yaml = """
title: Test Contains
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|contains: mimikatz
    condition: selection
"""
        rule = SigmaCollection.from_yaml(rule_yaml)
        queries = backend.convert(rule)

        assert len(queries) == 1
        assert "ILIKE '%mimikatz%'" in queries[0]

    def test_startswith_generates_ilike(self, backend):
        """Test that startswith modifier generates ILIKE."""
        rule_yaml = """
title: Test Startswith
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|startswith: cmd
    condition: selection
"""
        rule = SigmaCollection.from_yaml(rule_yaml)
        queries = backend.convert(rule)

        assert len(queries) == 1
        assert "ILIKE 'cmd%'" in queries[0]

    def test_endswith_generates_ilike(self, backend):
        """Test that endswith modifier generates ILIKE."""
        rule_yaml = """
title: Test Endswith
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|endswith: .exe
    condition: selection
"""
        rule = SigmaCollection.from_yaml(rule_yaml)
        queries = backend.convert(rule)

        assert len(queries) == 1
        assert "ILIKE '%.exe'" in queries[0]

    def test_regex_generates_regexp_matches(self, backend):
        """Test that regex modifier generates regexp_matches."""
        rule_yaml = """
title: Test Regex
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|re: 'powershell.*-enc'
    condition: selection
"""
        rule = SigmaCollection.from_yaml(rule_yaml)
        queries = backend.convert(rule)

        assert len(queries) == 1
        assert "regexp_matches" in queries[0]

    def test_default_table_name(self, backend):
        """Test default table name is 'logs'."""
        rule = SigmaCollection.from_yaml(SAMPLE_RULE)
        queries = backend.convert(rule)

        assert "FROM logs WHERE" in queries[0]


class TestPipelines:
    """Tests for processing pipelines."""

    def test_splunk_sysmon_pipeline(self):
        """Test splunk_sysmon pipeline is an identity mapping."""
        pipeline = splunk_sysmon()
        assert pipeline.name == "Splunk Sysmon TA Fields"
        # Should have no transformations
        assert len(pipeline.items) == 0

    def test_elastic_ecs_pipeline(self):
        """Test elastic_ecs pipeline maps fields correctly."""
        pipeline = elastic_ecs()
        assert pipeline.name == "Elastic ECS"
        # Should have field mappings
        assert len(pipeline.items) > 0

    def test_elastic_ecs_field_mapping(self):
        """Test that ECS pipeline maps Sigma fields to ECS fields."""
        backend = DuckDBBackend(processing_pipeline=elastic_ecs())

        rule = SigmaCollection.from_yaml(SAMPLE_RULE)
        queries = backend.convert(rule)

        assert len(queries) == 1
        # ECS maps CommandLine -> process.command_line
        assert "process.command_line" in queries[0]
