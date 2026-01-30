"""Directory validation utilities for CI testing."""

from __future__ import annotations

import logging
from pathlib import Path

from .backend import DuckDBBackend
from .log_index import LogIndex, ValidationResult

logger = logging.getLogger(__name__)


def validate_rules_directory(
    rules_dir: Path | str,
    logs_dir: Path | str,
    pattern: str = "**/*.yml",
) -> list[ValidationResult]:
    """Validate all Sigma rules in a directory against log files.

    Args:
        rules_dir: Directory containing Sigma rule files
        logs_dir: Directory containing JSON log files
        pattern: Glob pattern for rule files

    Returns:
        List of ValidationResult for each rule
    """
    # Load logs
    index = LogIndex()
    loaded = index.load_directory(logs_dir)
    logger.info(f"Loaded {loaded} logs from {logs_dir}")

    # Create backend
    backend = DuckDBBackend()

    # Validate each rule
    results = []
    for rule_path in sorted(Path(rules_dir).glob(pattern)):
        result = backend.validate_rule_file(rule_path, index)
        results.append(result)
        status = "PASS" if result.has_matches else "NO_MATCH"
        if result.errors:
            status = "ERROR"
        logger.info(f"{status}: {rule_path.name} ({result.match_count} matches)")

    return results
