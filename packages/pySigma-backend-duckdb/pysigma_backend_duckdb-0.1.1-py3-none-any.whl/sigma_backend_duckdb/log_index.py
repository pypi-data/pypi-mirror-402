"""Log index for loading and querying JSON log files with DuckDB."""

from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a Sigma rule against log data."""

    rule_title: str
    rule_id: str | None
    query: str
    total_logs: int
    match_count: int
    matched_logs: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if validation ran without errors."""
        return len(self.errors) == 0

    @property
    def has_matches(self) -> bool:
        """Check if the rule matched any logs."""
        return self.match_count > 0


class LogIndex:
    """Index of JSON log files for querying with DuckDB.

    Provides efficient loading and querying of log files for
    Sigma rule validation.
    """

    def __init__(self):
        self._logs: list[dict[str, Any]] = []
        self._temp_file: Path | None = None
        self._connection: duckdb.DuckDBPyConnection | None = None

    def add_log(self, log: dict[str, Any]) -> None:
        """Add a single log entry."""
        self._logs.append(log)
        self._invalidate_connection()

    def add_logs(self, logs: list[dict[str, Any]]) -> None:
        """Add multiple log entries."""
        self._logs.extend(logs)
        self._invalidate_connection()

    def load_json_file(self, path: Path | str) -> int:
        """Load logs from a JSON file.

        Supports:
        - Single object: {"@timestamp": "...", ...}
        - Array of objects: [{"@timestamp": "..."}, ...]
        - Newline-delimited JSON (NDJSON)

        Returns:
            Number of logs loaded
        """
        content = Path(path).read_text()
        count = 0

        # Try standard JSON first
        try:
            data = json.loads(content)
            if isinstance(data, list):
                self._logs.extend(data)
                count = len(data)
            elif isinstance(data, dict):
                self._logs.append(data)
                count = 1
            self._invalidate_connection()
            return count
        except json.JSONDecodeError:
            pass

        # Try NDJSON
        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                self._logs.append(data)
                count += 1
            except json.JSONDecodeError:
                continue

        self._invalidate_connection()
        return count

    def load_directory(self, directory: Path | str, pattern: str = "**/*.json") -> int:
        """Load all JSON files from a directory recursively.

        Returns:
            Total number of logs loaded
        """
        total = 0
        for path in sorted(Path(directory).glob(pattern)):
            loaded = self.load_json_file(path)
            logger.debug(f"Loaded {loaded} logs from {path.name}")
            total += loaded
        return total

    def clear(self) -> None:
        """Clear all entries from the index."""
        self._logs.clear()
        self._invalidate_connection()

    def _invalidate_connection(self) -> None:
        """Invalidate cached connection when data changes."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
        if self._temp_file is not None:
            self._temp_file.unlink(missing_ok=True)
            self._temp_file = None

    def get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create a DuckDB connection with the log data loaded."""
        if self._connection is not None:
            return self._connection

        if not self._logs:
            # Return empty connection
            self._connection = duckdb.connect(":memory:")
            self._connection.execute("CREATE TABLE logs (dummy INTEGER)")
            return self._connection

        # Write logs to temp file for DuckDB to read
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(self._logs, f, default=str)
            self._temp_file = Path(f.name)

        self._connection = duckdb.connect(":memory:")
        self._connection.execute(
            f"CREATE TABLE logs AS SELECT * FROM read_json_auto('{self._temp_file}')"
        )

        return self._connection

    def __len__(self) -> int:
        return len(self._logs)

    def __del__(self):
        """Cleanup temp files."""
        self._invalidate_connection()
