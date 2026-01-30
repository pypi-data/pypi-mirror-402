"""pySigma DuckDB backend for local Sigma rule validation."""

from .backend import DuckDBBackend
from .pipelines import elastic_ecs, get_pipeline_for_format, splunk_sysmon

__all__ = [
    "DuckDBBackend",
    "splunk_sysmon",
    "elastic_ecs",
    "get_pipeline_for_format",
]
