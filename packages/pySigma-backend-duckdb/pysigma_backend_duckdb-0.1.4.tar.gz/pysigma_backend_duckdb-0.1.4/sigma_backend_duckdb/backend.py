"""DuckDB backend for Sigma rule validation against local JSON logs.

This module provides a pySigma-compatible backend that generates DuckDB SQL
queries for validating Sigma rules against local JSON log files in CI.

The backend is self-contained and does not depend on pySigma-backend-sqlite.
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar, Dict, List, Optional, Pattern, Tuple, Union

from sigma.conditions import (
    ConditionAND,
    ConditionFieldEqualsValueExpression,
    ConditionItem,
    ConditionNOT,
    ConditionOR,
    ConditionValueExpression,
)
from sigma.conversion.base import TextQueryBackend
from sigma.conversion.deferred import DeferredQueryExpression
from sigma.conversion.state import ConversionState
from sigma.correlations import (
    SigmaCorrelationConditionOperator,
    SigmaCorrelationRule,
    SigmaCorrelationTypeLiteral,
)
from sigma.exceptions import SigmaFeatureNotSupportedByBackendError
from sigma.processing.pipeline import ProcessingPipeline
from sigma.rule import SigmaRule
from sigma.types import (
    SigmaCIDRExpression,
    SigmaCompareExpression,
    SigmaString,
    SpecialChars,
    TimestampPart,
)

from .pipelines import splunk_sysmon


class DuckDBBackend(TextQueryBackend):
    """DuckDB-compatible backend for Sigma rule validation.

    This backend generates DuckDB SQL queries from Sigma rules for
    validating detection logic against local JSON log files.

    Features:
    - Dot notation for nested fields (process.command_line)
    - ILIKE for case-insensitive matching
    - regexp_matches() function for regex
    - Correlation rule support
    """

    name: ClassVar[str] = "DuckDB backend for local validation"
    formats: Dict[str, str] = {
        "default": "Plain DuckDB queries",
        "zircolite": "Zircolite JSON format",
    }
    requires_pipeline: bool = False

    # Correlation support
    correlation_methods: ClassVar[Dict[str, str]] = {
        "default": "Default DuckDB correlation using subqueries and window functions",
    }

    # Operator precedence
    precedence: ClassVar[Tuple[ConditionItem, ConditionItem, ConditionItem]] = (
        ConditionNOT,
        ConditionAND,
        ConditionOR,
    )
    parenthesize: bool = True
    group_expression: ClassVar[str] = "({expr})"

    # Generated query tokens
    token_separator: str = " "
    or_token: ClassVar[str] = "OR"
    and_token: ClassVar[str] = "AND"
    not_token: ClassVar[str] = "NOT"
    eq_token: ClassVar[str] = "="

    # Field quoting - use double quotes for DuckDB fields
    field_quote: ClassVar[str] = '"'
    field_quote_pattern: ClassVar[Pattern] = re.compile(r"^[a-zA-Z0-9_]+$")
    field_quote_pattern_negation: ClassVar[bool] = True

    # String quoting
    str_quote: ClassVar[str] = "'"

    # DuckDB ILIKE doesn't need escape clause - backslashes are literal
    escape_char: ClassVar[str] = ""
    wildcard_multi: ClassVar[str] = "%"
    wildcard_single: ClassVar[str] = "_"

    # GLOB wildcards for case-sensitive matching
    wildcard_glob: ClassVar[str] = "*"
    wildcard_glob_single: ClassVar[str] = "?"

    add_escaped: ClassVar[str] = ""
    bool_values: ClassVar[Dict[bool, str]] = {
        True: "true",
        False: "false",
    }

    # DuckDB uses ILIKE for case-insensitive pattern matching (no ESCAPE needed)
    startswith_expression: ClassVar[str] = "{field} ILIKE '{value}%'"
    endswith_expression: ClassVar[str] = "{field} ILIKE '%{value}'"
    contains_expression: ClassVar[str] = "{field} ILIKE '%{value}%'"
    wildcard_match_expression: ClassVar[str] = "{field} ILIKE '{value}'"
    wildcard_match_str_expression: ClassVar[str] = "{field} ILIKE '{value}'"

    field_exists_expression: ClassVar[str] = "{field} IS NOT NULL"

    # DuckDB regex using regexp_matches function
    re_expression: ClassVar[str] = "regexp_matches({field}, '{regex}')"
    re_escape_char: ClassVar[str] = ""
    re_escape: ClassVar[Tuple[str, ...]] = ()
    re_escape_escape_char: bool = True
    re_flag_prefix: bool = True

    # Case-sensitive matching using GLOB (DuckDB supports this)
    case_sensitive_match_expression: ClassVar[str] = "{field} GLOB {value}"

    # Numeric comparison operators
    compare_op_expression: ClassVar[str] = "{field} {operator} {value}"
    compare_operators: ClassVar[Dict[SigmaCompareExpression.CompareOperators, str]] = {
        SigmaCompareExpression.CompareOperators.LT: "<",
        SigmaCompareExpression.CompareOperators.LTE: "<=",
        SigmaCompareExpression.CompareOperators.GT: ">",
        SigmaCompareExpression.CompareOperators.GTE: ">=",
    }

    # Field reference expressions
    field_equals_field_expression: ClassVar[Optional[str]] = "{field1}={field2}"
    field_equals_field_startswith_expression: ClassVar[Optional[str]] = (
        "{field1} ILIKE {field2} || '%'"
    )
    field_equals_field_endswith_expression: ClassVar[Optional[str]] = (
        "{field1} ILIKE '%' || {field2}"
    )
    field_equals_field_contains_expression: ClassVar[Optional[str]] = (
        "{field1} ILIKE '%' || {field2} || '%'"
    )
    field_equals_field_escaping_quoting: Tuple[bool, bool] = (True, True)

    # Timestamp part expressions for time modifiers (DuckDB syntax)
    field_timestamp_part_expression: ClassVar[Optional[str]] = (
        "EXTRACT({timestamp_part} FROM {field})"
    )
    timestamp_part_mapping: ClassVar[Optional[Dict[TimestampPart, str]]] = {
        TimestampPart.MINUTE: "MINUTE",
        TimestampPart.HOUR: "HOUR",
        TimestampPart.DAY: "DAY",
        TimestampPart.WEEK: "WEEK",
        TimestampPart.MONTH: "MONTH",
        TimestampPart.YEAR: "YEAR",
    }

    # Null expressions
    field_null_expression: ClassVar[str] = "{field} IS NULL"

    # Field value in list
    convert_or_as_in: ClassVar[bool] = False
    convert_and_as_in: ClassVar[bool] = False
    in_expressions_allow_wildcards: ClassVar[bool] = False
    field_in_list_expression: ClassVar[str] = "{field} {op} ({list})"
    or_in_operator: ClassVar[str] = "IN"
    list_separator: ClassVar[str] = ", "

    # Query finalization
    deferred_start: ClassVar[str] = ""
    deferred_separator: ClassVar[str] = ""
    deferred_only_query: ClassVar[str] = ""

    # ========== Correlation Rule Templates ==========
    # DuckDB correlation queries using window functions and subqueries

    correlation_search_single_rule_expression: ClassVar[Optional[str]] = (
        "SELECT * FROM logs WHERE {query}{normalization}"
    )
    correlation_search_multi_rule_expression: ClassVar[Optional[str]] = "{queries}"
    correlation_search_multi_rule_query_expression: ClassVar[Optional[str]] = (
        "SELECT *, '{ruleid}' AS sigma_rule_id FROM logs WHERE {query}{normalization}"
    )
    correlation_search_multi_rule_query_expression_joiner: ClassVar[Optional[str]] = " UNION ALL "

    correlation_search_field_normalization_expression: ClassVar[Optional[str]] = (
        "{field} AS {alias}"
    )
    correlation_search_field_normalization_expression_joiner: ClassVar[Optional[str]] = ", "

    timespan_seconds: ClassVar[bool] = True

    groupby_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": " GROUP BY {fields}",
    }
    groupby_field_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "{field}",
    }
    groupby_field_expression_joiner: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", ",
    }
    groupby_expression_nofield: ClassVar[Optional[Dict[str, str]]] = {
        "default": "",
    }

    # Event count correlation
    event_count_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    event_count_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", COUNT(*) AS event_count",
    }
    event_count_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "event_count {op} {count}",
    }

    # Value count correlation
    value_count_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    value_count_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", COUNT(DISTINCT {field}) AS value_count",
    }
    value_count_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "value_count {op} {count}",
    }

    # Temporal correlation (DuckDB uses epoch_ms for timestamp arithmetic)
    temporal_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition} AND (epoch_ms(last_event) - epoch_ms(first_event)) / 1000.0 <= {timespan}",
    }
    temporal_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", COUNT(DISTINCT sigma_rule_id) AS rule_count, MIN(timestamp) AS first_event, MAX(timestamp) AS last_event",
    }
    temporal_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "rule_count {op} {count}",
    }

    # Temporal ordered correlation
    temporal_ordered_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition} AND (epoch_ms(last_event) - epoch_ms(first_event)) / 1000.0 <= {timespan}",
    }
    temporal_ordered_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", STRING_AGG(sigma_rule_id, ',' ORDER BY timestamp) AS rule_sequence, COUNT(DISTINCT sigma_rule_id) AS rule_count, MIN(timestamp) AS first_event, MAX(timestamp) AS last_event",
    }
    temporal_ordered_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "rule_count {op} {count}",
    }

    # Value sum correlation
    value_sum_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    value_sum_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", SUM({field}) AS value_sum",
    }
    value_sum_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "value_sum {op} {count}",
    }

    # Value avg correlation
    value_avg_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    value_avg_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", AVG({field}) AS value_avg",
    }
    value_avg_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "value_avg {op} {count}",
    }

    # Value percentile correlation (DuckDB has native percentile support)
    value_percentile_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    value_percentile_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", PERCENTILE_CONT({percentile} / 100.0) WITHIN GROUP (ORDER BY {field}) AS value_percentile",
    }
    value_percentile_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "value_percentile {op} {count}",
    }

    # Value median correlation (DuckDB supports MEDIAN directly)
    value_median_correlation_query: ClassVar[Optional[Dict[str, str]]] = {
        "default": "SELECT {select_fields}{aggregate} FROM ({search}) AS subquery{groupby} HAVING {condition}",
    }
    value_median_aggregation_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", MEDIAN({field}) AS value_median",
    }
    value_median_condition_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "value_median {op} {count}",
    }

    # Correlation condition operator mapping
    correlation_condition_mapping: ClassVar[
        Optional[Dict[SigmaCorrelationConditionOperator, str]]
    ] = {
        SigmaCorrelationConditionOperator.LT: "<",
        SigmaCorrelationConditionOperator.LTE: "<=",
        SigmaCorrelationConditionOperator.GT: ">",
        SigmaCorrelationConditionOperator.GTE: ">=",
        SigmaCorrelationConditionOperator.EQ: "=",
        SigmaCorrelationConditionOperator.NEQ: "!=",
    }

    # Referenced rules expressions
    referenced_rules_expression: ClassVar[Optional[Dict[str, str]]] = {
        "default": "'{ruleid}'",
    }
    referenced_rules_expression_joiner: ClassVar[Optional[Dict[str, str]]] = {
        "default": ", ",
    }

    table = "logs"
    timestamp_field = "timestamp"

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

    def convert_correlation_rule_from_template(
        self,
        rule: SigmaCorrelationRule,
        correlation_type: SigmaCorrelationTypeLiteral,
        method: str,
    ) -> List[str]:
        """Override to add {select_fields} placeholder that properly handles GROUP BY.

        When GROUP BY is used, we select only the grouped fields (not SELECT *).
        Also substitutes the configurable timestamp_field in the generated query.
        """
        from sigma.exceptions import SigmaConversionError

        template = (
            getattr(self, f"{correlation_type}_correlation_query") or self.default_correlation_query
        )
        if template is None:
            raise NotImplementedError(
                f"Correlation rule type '{correlation_type}' is not supported by backend."
            )

        if method not in template:
            raise SigmaConversionError(
                rule,
                rule.source,
                f"Correlation method '{method}' is not supported by backend for correlation type '{correlation_type}'.",
            )

        search = self.convert_correlation_search(rule)

        # Determine select_fields based on whether GROUP BY is used
        if rule.group_by:
            # When GROUP BY is used, only select the grouped fields
            select_fields = ", ".join(self.escape_and_quote_field(f) for f in rule.group_by)
        else:
            # When no GROUP BY, we can use * since all rows aggregate to one
            select_fields = "*"

        # Get the aggregate expression and substitute the timestamp field
        aggregate = self.convert_correlation_aggregation_from_template(
            rule, correlation_type, method, search
        )
        # Replace hardcoded 'timestamp' with the configurable timestamp_field
        aggregate = aggregate.replace("timestamp", self.timestamp_field)

        query = template[method].format(
            search=search,
            typing=self.convert_correlation_typing(rule),
            timespan=self.convert_timespan(rule.timespan, method),
            aggregate=aggregate,
            condition=self.convert_correlation_condition_from_template(
                rule.condition, rule.rules, correlation_type, method
            ),
            groupby=self.convert_correlation_aggregation_groupby_from_template(
                rule.group_by, method
            ),
            select_fields=select_fields,
        )

        return [query]

    def convert_value_str(
        self,
        s: SigmaString,
        state: ConversionState,
        no_quote: bool = False,
        glob_wildcards: bool = False,
    ) -> str:
        """Convert a SigmaString into a plain string which can be used in query."""
        if glob_wildcards:
            converted = s.convert(
                escape_char=self.escape_char,
                wildcard_multi=self.wildcard_glob,
                wildcard_single=self.wildcard_glob_single,
                add_escaped=self.add_escaped,
                filter_chars=self.filter_chars,
            )
        else:
            converted = s.convert(
                escape_char=self.escape_char,
                wildcard_multi=self.wildcard_multi,
                wildcard_single=self.wildcard_single,
                add_escaped=self.add_escaped,
                filter_chars=self.filter_chars,
            )

        # Double single quotes for SQL
        converted = converted.replace("'", "''")

        if self.decide_string_quoting(s) and not no_quote:
            return self.quote_string(converted)
        else:
            return converted

    def convert_condition_field_eq_val_str(
        self, cond: ConditionFieldEqualsValueExpression, state: ConversionState
    ) -> Union[str, DeferredQueryExpression]:
        """Conversion of field = string value expressions."""
        try:
            remove_quote = True

            if (
                self.startswith_expression is not None
                and cond.value.endswith(SpecialChars.WILDCARD_MULTI)
                and not cond.value[:-1].contains_special()
            ):
                expr = self.startswith_expression
                value = cond.value[:-1]
            elif (
                self.endswith_expression is not None
                and cond.value.startswith(SpecialChars.WILDCARD_MULTI)
                and not cond.value[1:].contains_special()
            ):
                expr = self.endswith_expression
                value = cond.value[1:]
            elif (
                self.contains_expression is not None
                and cond.value.startswith(SpecialChars.WILDCARD_MULTI)
                and cond.value.endswith(SpecialChars.WILDCARD_MULTI)
                and not cond.value[1:-1].contains_special()
            ):
                expr = self.contains_expression
                value = cond.value[1:-1]
            elif self.wildcard_match_expression is not None and (
                cond.value.contains_special()
                or self.wildcard_multi in cond.value
                or self.wildcard_single in cond.value
            ):
                expr = self.wildcard_match_expression
                value = cond.value
            else:
                expr = "{field}" + self.eq_token + "{value}"
                value = cond.value
                remove_quote = False

            if remove_quote:
                return expr.format(
                    field=self.escape_and_quote_field(cond.field),
                    value=self.convert_value_str(value, state, remove_quote),
                )
            else:
                return expr.format(
                    field=self.escape_and_quote_field(cond.field),
                    value=self.convert_value_str(value, state),
                )
        except TypeError:
            raise NotImplementedError(
                "Field equals string value expressions with strings are not supported by the backend."
            )

    def convert_condition_field_eq_val_str_case_sensitive(
        self, cond: ConditionFieldEqualsValueExpression, state: ConversionState
    ) -> Union[str, DeferredQueryExpression]:
        """Conversion of case-sensitive field = string value expressions."""
        try:
            if (
                self.case_sensitive_startswith_expression is not None
                and cond.value.endswith(SpecialChars.WILDCARD_MULTI)
                and (
                    self.case_sensitive_startswith_expression_allow_special
                    or not cond.value[:-1].contains_special()
                )
            ):
                expr = self.case_sensitive_startswith_expression
                value = cond.value[:-1]
            elif (
                self.case_sensitive_endswith_expression is not None
                and cond.value.startswith(SpecialChars.WILDCARD_MULTI)
                and (
                    self.case_sensitive_endswith_expression_allow_special
                    or not cond.value[1:].contains_special()
                )
            ):
                expr = self.case_sensitive_endswith_expression
                value = cond.value[1:]
            elif (
                self.case_sensitive_contains_expression is not None
                and cond.value.startswith(SpecialChars.WILDCARD_MULTI)
                and cond.value.endswith(SpecialChars.WILDCARD_MULTI)
                and (
                    self.case_sensitive_contains_expression_allow_special
                    or not cond.value[1:-1].contains_special()
                )
            ):
                expr = self.case_sensitive_contains_expression
                value = cond.value[1:-1]
            elif self.case_sensitive_match_expression is not None:
                expr = self.case_sensitive_match_expression
                value = cond.value
            else:
                raise NotImplementedError(
                    "Case-sensitive string matching is not supported by backend."
                )

            return expr.format(
                field=self.escape_and_quote_field(cond.field),
                value=self.convert_value_str(value, state, no_quote=False, glob_wildcards=True),
                regex=self.convert_value_re(value.to_regex(self.add_escaped_re), state),
            )
        except TypeError:
            raise NotImplementedError(
                "Case-sensitive field equals string value expressions are not supported by the backend."
            )

    def convert_condition_field_eq_val_cidr(
        self, cond: ConditionFieldEqualsValueExpression, state: ConversionState
    ) -> Union[str, DeferredQueryExpression]:
        """Conversion of field matches CIDR value expressions."""
        cidr: SigmaCIDRExpression = cond.value
        expanded = cidr.expand()
        expanded_cond = ConditionOR(
            [
                ConditionFieldEqualsValueExpression(cond.field, SigmaString(network))
                for network in expanded
            ],
            cond.source,
        )
        return self.convert_condition(expanded_cond, state)

    def finalize_query_default(
        self,
        rule: Union[SigmaRule, SigmaCorrelationRule],
        query: str,
        index: int,
        state: ConversionState,
    ) -> Any:
        """Finalize query with DuckDB-compatible SQL."""
        # For correlation rules, the query is already complete
        if isinstance(rule, SigmaCorrelationRule):
            return query

        return f"SELECT * FROM {self.table} WHERE {query}"

    def finalize_query_zircolite(
        self,
        rule: Union[SigmaRule, SigmaCorrelationRule],
        query: str,
        index: int,
        state: ConversionState,
    ) -> Any:
        """Finalize query in Zircolite format."""
        # For correlation rules, use the query as-is
        if isinstance(rule, SigmaCorrelationRule):
            duckdb_query = query
        else:
            duckdb_query = f"SELECT * FROM logs WHERE {query}"

        rule_as_dict = rule.to_dict()

        zircolite_rule = {
            "title": rule_as_dict.get("title", ""),
            "id": rule_as_dict.get("id", ""),
            "status": rule_as_dict.get("status", ""),
            "description": rule_as_dict.get("description", ""),
            "author": rule_as_dict.get("author", ""),
            "tags": rule_as_dict.get("tags", []),
            "falsepositives": rule_as_dict.get("falsepositives", []),
            "level": rule_as_dict.get("level", ""),
            "rule": [duckdb_query],
            "filename": "",
        }
        return zircolite_rule

    def finalize_output_zircolite(self, queries: List[Dict]) -> str:
        """Finalize output for Zircolite format."""
        return json.dumps(list(queries))

    def convert_condition_val_str(
        self, cond: ConditionValueExpression, state: ConversionState
    ) -> Union[str, DeferredQueryExpression]:
        """Conversion of value-only strings."""
        raise SigmaFeatureNotSupportedByBackendError(
            "Value-only string expressions (Full Text Search or 'keywords' search) are not supported by the backend."
        )

    def convert_condition_val_num(
        self, cond: ConditionValueExpression, state: ConversionState
    ) -> Union[str, DeferredQueryExpression]:
        """Conversion of value-only numbers."""
        raise SigmaFeatureNotSupportedByBackendError(
            "Value-only number expressions (Full Text Search or 'keywords' search) are not supported by the backend."
        )
