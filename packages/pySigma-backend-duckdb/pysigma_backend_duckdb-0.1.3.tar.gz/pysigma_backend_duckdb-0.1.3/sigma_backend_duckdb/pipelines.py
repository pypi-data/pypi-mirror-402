"""Sigma processing pipelines for log schema transformations.

Provides pipelines that map Sigma rule fields to specific log schemas.
"""

from sigma.processing.conditions import (
    IncludeFieldCondition,
    LogsourceCondition,
)
from sigma.processing.pipeline import ProcessingItem, ProcessingPipeline
from sigma.processing.transformations import (
    DropDetectionItemTransformation,
    FieldMappingTransformation,
)


def splunk_sysmon() -> ProcessingPipeline:
    """Pipeline for Splunk with Sysmon TA field extraction.

    Splunk Sysmon TA extracts fields with the same names as Sigma uses
    (Image, CommandLine, ParentImage, etc.) so this is essentially an
    identity mapping. No field transformation needed.
    """
    return ProcessingPipeline(
        name="Splunk Sysmon TA Fields",
        priority=20,
        items=[
            # No transformations needed - Splunk Sysmon TA field names
            # match Sigma field names directly
        ],
    )


def elastic_ecs() -> ProcessingPipeline:
    """Pipeline for Elasticsearch with ECS (Elastic Common Schema).

    Maps Sigma fields to ECS field names as produced by Filebeat/Elastic Agent
    with the Sysmon module. Fields use process.*, user.*, host.* structure.
    """
    return ProcessingPipeline(
        name="Elastic ECS",
        priority=20,
        items=[
            # Filebeat with ECS mapping stores process fields under process.*
            ProcessingItem(
                identifier="elastic_ecs_process_fields",
                transformation=FieldMappingTransformation(
                    {
                        "Image": "process.executable",
                        "CommandLine": "process.command_line",
                        "ParentImage": "process.parent.executable",
                        "ParentCommandLine": "process.parent.command_line",
                        "ProcessId": "process.pid",
                        "ParentProcessId": "process.parent.pid",
                        "CurrentDirectory": "process.working_directory",
                    }
                ),
                rule_conditions=[
                    LogsourceCondition(category="process_creation"),
                ],
            ),
            ProcessingItem(
                identifier="elastic_ecs_user",
                transformation=FieldMappingTransformation(
                    {
                        "User": "user.name",
                    }
                ),
                rule_conditions=[
                    LogsourceCondition(category="process_creation"),
                ],
            ),
            ProcessingItem(
                identifier="elastic_ecs_host",
                transformation=FieldMappingTransformation(
                    {
                        "ComputerName": "host.name",
                        "Computer": "host.name",
                    }
                ),
            ),
            # Drop OriginalFileName detection items - often not present in logs
            ProcessingItem(
                identifier="drop_originalfilename",
                transformation=DropDetectionItemTransformation(),
                field_name_conditions=[
                    IncludeFieldCondition(fields=["OriginalFileName"]),
                ],
                rule_conditions=[
                    LogsourceCondition(category="process_creation"),
                ],
            ),
        ],
    )


def get_pipeline_for_format(format_name: str) -> ProcessingPipeline:
    """Get the appropriate pipeline for a log format.

    Args:
        format_name: One of 'splunk', 'elastic', 'ecs'

    Returns:
        ProcessingPipeline for the format
    """
    pipelines = {
        "splunk": splunk_sysmon,
        "elastic": elastic_ecs,
        "ecs": elastic_ecs,  # ECS is same as elastic
    }

    if format_name not in pipelines:
        raise ValueError(f"Unknown format: {format_name}. Use: {list(pipelines.keys())}")

    return pipelines[format_name]()
