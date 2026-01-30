"""Tests for DuckDB backend."""

import json
from pathlib import Path

import pytest

from sigma_backend_duckdb import (
    DuckDBBackend,
    LogIndex,
    elastic_ecs,
    splunk_sysmon,
)

# Test data - Splunk Sysmon format (matches default splunk_sysmon pipeline)
SAMPLE_LOGS = [
    {
        "CommandLine": "powershell.exe -e JgAgACgAZwBjAG0AIAAoACcAaQBlAHsAMAB9ACcA",
        "Image": "C:\\Windows\\System32\\powershell.exe",
        "ProcessName": "powershell.exe",
        "_time": "2026-01-21T13:09:55Z",
        "ComputerName": "WIN-SERVER",
    },
    {
        "CommandLine": "cmd.exe /c dir",
        "Image": "C:\\Windows\\System32\\cmd.exe",
        "ProcessName": "cmd.exe",
        "_time": "2026-01-21T13:10:00Z",
        "ComputerName": "WIN-SERVER",
    },
    {
        "CommandLine": "powershell.exe Get-Process",
        "Image": "C:\\Windows\\System32\\powershell.exe",
        "ProcessName": "powershell.exe",
        "_time": "2026-01-21T13:11:00Z",
        "ComputerName": "WIN-SERVER",
    },
]

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


class TestLogIndex:
    """Tests for LogIndex class."""

    def test_add_logs(self):
        """Test adding logs to index."""
        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)
        assert len(index) == 3

    def test_add_single_log(self):
        """Test adding a single log entry."""
        index = LogIndex()
        index.add_log(SAMPLE_LOGS[0])
        assert len(index) == 1

    def test_clear(self):
        """Test clearing the index."""
        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)
        index.clear()
        assert len(index) == 0

    def test_load_json_file(self, tmp_path):
        """Test loading logs from a JSON file."""
        log_file = tmp_path / "test_logs.json"
        log_file.write_text(json.dumps(SAMPLE_LOGS))

        index = LogIndex()
        count = index.load_json_file(log_file)

        assert count == 3
        assert len(index) == 3

    def test_load_single_object(self, tmp_path):
        """Test loading a single JSON object (not array)."""
        log_file = tmp_path / "single_log.json"
        log_file.write_text(json.dumps(SAMPLE_LOGS[0]))

        index = LogIndex()
        count = index.load_json_file(log_file)

        assert count == 1
        assert len(index) == 1

    def test_load_ndjson(self, tmp_path):
        """Test loading NDJSON (newline-delimited JSON)."""
        log_file = tmp_path / "logs.ndjson"
        ndjson = "\n".join(json.dumps(log) for log in SAMPLE_LOGS)
        log_file.write_text(ndjson)

        index = LogIndex()
        count = index.load_json_file(log_file)

        assert count == 3
        assert len(index) == 3

    def test_load_directory(self, tmp_path):
        """Test loading all JSON files from a directory."""
        (tmp_path / "logs1.json").write_text(json.dumps(SAMPLE_LOGS[:2]))
        (tmp_path / "logs2.json").write_text(json.dumps(SAMPLE_LOGS[2:]))

        index = LogIndex()
        count = index.load_directory(tmp_path)

        assert count == 3
        assert len(index) == 3

    def test_get_connection(self):
        """Test getting DuckDB connection."""
        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)

        con = index.get_connection()
        result = con.execute("SELECT COUNT(*) FROM logs").fetchone()

        assert result[0] == 3


class TestDuckDBBackend:
    """Tests for DuckDBBackend class."""

    @pytest.fixture
    def backend(self):
        return DuckDBBackend()

    @pytest.fixture
    def index_with_logs(self):
        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)
        return index

    def test_validate_rule_matches(self, backend, index_with_logs):
        """Test that a rule matches expected logs."""
        result = backend.validate_rule(SAMPLE_RULE, index_with_logs)

        assert result.success
        assert result.match_count == 1
        assert result.total_logs == 3
        assert len(result.errors) == 0

    def test_validate_rule_no_matches(self, backend, index_with_logs):
        """Test a rule that doesn't match any logs."""
        rule = """
title: Test No Match
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        CommandLine|contains: mimikatz
    condition: selection
"""
        result = backend.validate_rule(rule, index_with_logs)

        assert result.success
        assert result.match_count == 0
        assert result.total_logs == 3

    def test_validate_invalid_rule(self, backend, index_with_logs):
        """Test validation of invalid rule."""
        invalid_rule = """
title: Invalid Rule
# Missing logsource and detection
"""
        result = backend.validate_rule(invalid_rule, index_with_logs)

        assert not result.success
        assert len(result.errors) > 0

    def test_query_generation(self, backend):
        """Test that correct SQL query is generated."""
        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)

        result = backend.validate_rule(SAMPLE_RULE, index)

        # Check query uses Splunk Sysmon field names (identity mapping)
        assert "CommandLine" in result.query
        assert "SELECT * FROM logs WHERE" in result.query

    def test_validate_rule_file(self, backend, tmp_path):
        """Test validating a rule from file."""
        rule_file = tmp_path / "test_rule.yml"
        rule_file.write_text(SAMPLE_RULE)

        index = LogIndex()
        index.add_logs(SAMPLE_LOGS)

        result = backend.validate_rule_file(rule_file, index)

        assert result.success
        assert result.match_count == 1


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


class TestRealTestData:
    """Tests using real test data from tests/data/ directory."""

    DATA_DIR = Path(__file__).parent / "data"

    @pytest.fixture
    def backend(self):
        return DuckDBBackend()

    def test_t1087_002_splunk_logs(self, backend):
        """Test T1087.002 rule against Splunk format logs."""
        test_dir = self.DATA_DIR / "T1087.002-0"
        rule_path = test_dir / "rule.yml"
        logs_path = test_dir / "logs_splunk.json"

        # Load logs
        index = LogIndex()
        count = index.load_json_file(logs_path)
        assert count == 2, "Expected 2 log entries"

        # Validate rule
        result = backend.validate_rule_file(rule_path, index)

        assert result.success, f"Validation failed: {result.errors}"
        assert result.match_count == 2, f"Expected 2 matches, got {result.match_count}"
        assert result.rule_title == "Domain Account Enumeration via Net Command"

        # Verify matched logs contain expected commands
        commands = [log.get("CommandLine", "") for log in result.matched_logs]
        assert any("user /domain" in cmd for cmd in commands)
        assert any("group /domain" in cmd for cmd in commands)

    def test_t1087_002_elastic_logs(self):
        """Test T1087.002 rule against Elastic ECS format logs."""
        test_dir = self.DATA_DIR / "T1087.002-0"
        rule_path = test_dir / "rule.yml"
        logs_path = test_dir / "logs_elastic.json"

        # Use ECS pipeline for Elastic logs
        backend = DuckDBBackend(processing_pipeline=elastic_ecs())

        # Load logs
        index = LogIndex()
        count = index.load_json_file(logs_path)
        assert count == 2, "Expected 2 log entries"

        # Validate rule
        result = backend.validate_rule_file(rule_path, index)

        assert result.success, f"Validation failed: {result.errors}"
        assert result.match_count == 2, f"Expected 2 matches, got {result.match_count}"

    def test_wrong_pipeline_causes_query_error(self):
        """Test that using wrong pipeline causes query errors (field not found)."""
        test_dir = self.DATA_DIR / "T1087.002-0"
        rule_path = test_dir / "rule.yml"
        # Use Splunk logs but ECS pipeline - fields won't exist
        logs_path = test_dir / "logs_splunk.json"

        # ECS pipeline maps CommandLine -> process.command_line
        # but Splunk logs have CommandLine at top level (no nested process struct)
        backend = DuckDBBackend(processing_pipeline=elastic_ecs())

        index = LogIndex()
        index.load_json_file(logs_path)

        result = backend.validate_rule_file(rule_path, index)

        # DuckDB fails because process.executable field doesn't exist
        assert not result.success, "Should fail with wrong pipeline"
        assert len(result.errors) > 0
        assert "process" in result.errors[0].lower()
