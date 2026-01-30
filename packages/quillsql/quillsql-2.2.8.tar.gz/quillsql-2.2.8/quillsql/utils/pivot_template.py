"""
Pivot Template System - SDK SIDE

This file contains all the logic needed on the SDK to:
1. Hydrate pivot query templates with actual distinct values
2. Parse distinct values from different database result formats
3. Validate templates before hydration

This runs on the customer's Python SDK where customer data is accessible.
Takes templates from server and populates them with actual data.
"""

import json
import re
from typing import List, Dict, Any, Optional, TypedDict

# Constants
MAX_PIVOT_UNIQUE_VALUES = 250
PIVOT_COLUMN_MARKER = "{{QUILL_PIVOT_COLUMNS}}"
PIVOT_COLUMN_ALIAS_MARKER = "{{QUILL_PIVOT_COLUMN_ALIASES}}"


# Types
class PivotAggregation(TypedDict, total=False):
    aggregationType: str
    valueField: Optional[str]
    valueFieldType: Optional[str]
    valueField2: Optional[str]
    valueField2Type: Optional[str]


class PivotConfig(TypedDict, total=False):
    requiresDistinctValues: bool
    columnField: Optional[str]
    rowField: Optional[str]
    rowFieldType: Optional[str]
    aggregations: List[PivotAggregation]
    databaseType: str
    dateBucket: Optional[str]
    pivotType: str
    sort: Optional[bool]
    sortField: Optional[str]
    sortDirection: Optional[str]
    rowLimit: Optional[int]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def process_single_quotes(value: str, database_type: str) -> str:
    """Process single quotes based on database type."""
    if database_type.lower() in ["postgresql", "snowflake", "clickhouse"]:
        return value.replace("'", "''")
    return value.replace("'", "\\'")


def process_agg_type(agg_type: str, has_column_field: bool = False) -> str:
    """Process aggregation type."""
    if agg_type == "count" and has_column_field:
        return "SUM"
    return "AVG" if agg_type and agg_type.lower() == "average" else (agg_type.lower() if agg_type else "")


def replace_bigquery_special_characters(column: str) -> str:
    """Replace BigQuery special characters."""
    return column.replace("/", "quill_forward_slash")


def process_column_reference(
    column: str,
    database_type: str,
    fallback_on_null: Optional[str] = None,
    is_column_field_alias: bool = False,
    is_value_field_alias: bool = False
) -> str:
    """Process column reference based on database type."""
    db = database_type.lower()
    
    if db in ["postgresql", "clickhouse"]:
        if column == "":
            return f'"{fallback_on_null}"' if fallback_on_null else '"_"'
        if is_column_field_alias:
            return f'"{column.replace(chr(34), "")}"'
        column_parts = column.split(".")
        if len(column_parts) > 1:
            return '"' + '","'.join([part.replace('"', '') for part in column_parts]) + '"'
        return f'"{column.replace(chr(34), "")}"'
    
    elif db == "mysql":
        if column == "":
            return fallback_on_null if fallback_on_null else "_"
        if is_column_field_alias:
            return f"`{column.replace('`', '').replace(chr(34), '')}`"
        column_parts = column.split(".")
        if len(column_parts) > 1:
            return "`" + "`.`".join([part.replace("`", "") for part in column_parts]) + "`"
        return f"`{column.replace('`', '')}`"
    
    elif db == "snowflake":
        if column == "":
            return fallback_on_null if fallback_on_null else "_"
        if is_column_field_alias:
            return f'"{column.replace(chr(34), "")}"'
        if is_value_field_alias:
            cleaned_column = column.replace(")", "").replace("(", "_")
            return cleaned_column
        return column
    
    elif db == "bigquery":
        if column == "":
            return f"`{fallback_on_null}`" if fallback_on_null else "`_`"
        if is_column_field_alias:
            return f"`{replace_bigquery_special_characters(column)}`"
        column_parts = column.split(".")
        if len(column_parts) > 1:
            return "`" + "`.`".join([part for part in column_parts]) + "`"
        return f"`{column}`"
    
    elif db == "mssql":
        if column == "":
            return f"[{fallback_on_null}]" if fallback_on_null else "[_]"
        if is_column_field_alias:
            return f"[{column}]"
        column_parts = column.split(".")
        if len(column_parts) > 1:
            return "[" + "].[".join([part for part in column_parts]) + "]"
        return f"[{column}]"
    
    elif db == "databricks":
        if column == "":
            return f"`{fallback_on_null}`" if fallback_on_null else "`_`"
        if is_column_field_alias:
            return f"`{column}`"
        column_parts = column.split(".")
        if len(column_parts) > 1:
            return "`" + "`.`".join([part for part in column_parts]) + "`"
        return f"`{column}`"
    
    else:
        return column


def process_value_field(agg_type: str, database_type: str, value_field: str) -> str:
    """Process value field based on aggregation type."""
    if agg_type in ["min", "max"] or (agg_type and agg_type.lower() == "average"):
        return f"{process_column_reference(value_field, database_type)} ELSE null"
    if agg_type == "count":
        return "1 ELSE 0"
    return f"{process_column_reference(value_field, database_type)} ELSE 0" if value_field else "1 ELSE 0"


# ============================================================================
# DISTINCT VALUES PARSING
# ============================================================================


def parse_distinct_values(query_result: Dict[str, Any], database_type: str) -> List[str]:
    """
    Parses distinct values from database query results.
    Different databases return different formats.
    """
    if not query_result or not query_result.get("rows") or len(query_result["rows"]) == 0:
        return []
    
    row = query_result["rows"][0]
    distinct_values = []
    
    db = database_type.lower()
    
    if db in ["postgresql", "bigquery", "snowflake", "databricks", "clickhouse"]:
        # These return arrays in string_values field
        if "string_values" in row:
            if isinstance(row["string_values"], list):
                distinct_values = row["string_values"]
            elif isinstance(row["string_values"], str):
                # Handle JSON string arrays
                try:
                    distinct_values = json.loads(row["string_values"])
                except:
                    distinct_values = []
    
    elif db == "mysql":
        # MySQL returns JSON_ARRAYAGG which should be an array
        if "string_values" in row:
            if isinstance(row["string_values"], list):
                distinct_values = row["string_values"]
            elif isinstance(row["string_values"], str):
                try:
                    distinct_values = json.loads(row["string_values"])
                except:
                    distinct_values = []
    
    elif db == "mssql":
        # MS SQL returns comma-separated string
        if "string_values" in row and isinstance(row["string_values"], str):
            distinct_values = [v.strip() for v in row["string_values"].split(",")]
    
    else:
        distinct_values = []
    
    # Filter out null/undefined/empty values
    return [value for value in distinct_values if value is not None and value != ""]


# ============================================================================
# MATCH CASING FUNCTION
# ============================================================================


def match_casing(text: Optional[str], template: Optional[str]) -> str:
    """Matches the casing of text to template."""
    if not text or not template:
        return text or ""
    
    # Detect patterns
    def is_title_case(s: str) -> bool:
        return bool(re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', s))
    
    def is_camel_case(s: str) -> bool:
        return bool(re.match(r'^[a-z]+([A-Z][a-z]*)*$', s))
    
    def is_snake_case(s: str) -> bool:
        return bool(re.match(r'^[a-z0-9]+(_[a-z0-9]+)*$', s))
    
    def is_all_lower_case(s: str) -> bool:
        return bool(re.match(r'^[a-z]+$', s))
    
    def is_all_upper_case(s: str) -> bool:
        return bool(re.match(r'^[A-Z]+$', s))
    
    def is_capitalized(s: str) -> bool:
        return bool(re.match(r'^[A-Z][a-z]*$', s))
    
    def is_screaming_snake_case(s: str) -> bool:
        return bool(re.match(r'^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$', s))
    
    # Convert functions
    def to_title_case(s: str) -> str:
        return ''.join(word.capitalize() for word in re.split(r'[_\s]+', s.lower()))
    
    def to_camel_case(s: str) -> str:
        return re.sub(r'_(.)', lambda m: m.group(1).upper(), s.lower())
    
    def to_snake_case(s: str) -> str:
        return re.sub(r'[A-Z]', lambda m: f'_{m.group(0).lower()}', s)
    
    def to_screaming_snake_case(s: str) -> str:
        result = re.sub(r'([A-Z])', r'_\1', s)
        result = result.lstrip('_')
        return result.upper()
    
    # Match casing
    if is_title_case(template):
        return to_title_case(text)
    elif is_camel_case(template):
        return to_camel_case(text)
    elif is_snake_case(template):
        return to_snake_case(text)
    elif is_all_lower_case(template):
        return text.lower()
    elif is_all_upper_case(template):
        return text.upper()
    elif is_capitalized(template):
        return text.capitalize()
    elif is_screaming_snake_case(template):
        return to_screaming_snake_case(text)
    else:
        return text  # Default case if no specific pattern is detected


# ============================================================================
# TEMPLATE HYDRATION
# ============================================================================


def hydrate_pivot_template(
    template: str,
    distinct_values: List[str],
    config: PivotConfig
) -> str:
    """
    Hydrates a pivot query template with actual distinct values.
    This function should be called in the Python SDK after fetching distinct values.
    
    Args:
        template: The SQL template string containing markers
        distinct_values: Array of distinct values fetched from the database
        config: config about the pivot configuration
    
    Returns:
        Hydrated SQL query string ready to execute
    """
    column_field = config.get("columnField")
    row_field = config.get("rowField")
    aggregations = config.get("aggregations", [])
    database_type = config.get("databaseType", "postgresql")
    
    # If this pivot doesn't require distinct values, return as-is
    if not config.get("requiresDistinctValues") or not column_field or not row_field:
        return template
    
    # Filter and limit distinct values
    filtered_values = [
        value for value in distinct_values
        if value is not None and value != ""
    ][:MAX_PIVOT_UNIQUE_VALUES]
    
    # Get properly quoted column references
    column_field_alias = process_column_reference(
        column_field,
        database_type,
        None,
        False,
        True
    )
    
    row_field_alias = process_column_reference(
        row_field,
        database_type,
        None,
        False,
        True
    )
    
    # Generate column aliases for SELECT in quill_alias CTE
    column_aliases = []
    column_aliases.append(
        f"{process_column_reference(row_field, database_type, None, True)} AS {row_field_alias}"
    )
    
    # Generate CASE WHEN columns for each aggregation
    case_when_columns = []
    seen_aggs: Dict[str, Dict[str, int]] = {}
    
    for current_agg in aggregations:
        agg_type = current_agg.get("aggregationType", "")
        value_field = current_agg.get("valueField", "")
        
        # Track duplicate aggregation combos for disambiguation
        if agg_type in seen_aggs and value_field in seen_aggs[agg_type]:
            seen_aggs[agg_type][value_field] += 1
        else:
            if agg_type not in seen_aggs:
                seen_aggs[agg_type] = {}
            seen_aggs[agg_type][value_field] = 1
        
        disambiguation_index = str(seen_aggs[agg_type][value_field])
        if disambiguation_index == "1":
            disambiguation_index = ""
        
        value_field_alias = process_column_reference(
            current_agg.get("valueField") or row_field or "count",
            database_type,
            None,
            False,
            True
        )
        
        value_alias_substring = ""
        if current_agg.get("valueField"):
            value_alias_substring = f"{process_column_reference(current_agg['valueField'], database_type, None, True)} AS {value_field_alias}"
        
        # Handle disambiguation for multiple aggregations
        total_seen = sum(seen_aggs[agg_type].values())
        disambiguation_field = ""
        if total_seen > 1:
            disambiguation_field = f"_{current_agg.get('valueField', '')}{disambiguation_index}"
        
        disambiguation = ""
        if len(aggregations) > 1:
            if disambiguation_field:
                disambiguation = f"{disambiguation_field}_{match_casing(agg_type, current_agg.get('valueField'))}"
            else:
                disambiguation = f"_{agg_type}"
        
        # Wrap boolean fields in CASE WHEN
        value_expr = ""
        if current_agg.get("valueFieldType") == "bool":
            value_expr = f"CASE WHEN {value_field_alias} THEN 1 ELSE 0 END"
        else:
            value_expr = process_value_field(
                agg_type,
                database_type,
                value_field_alias
            )
        
        # Handle percentage aggregations specially
        if agg_type == "percentage":
            value_field2 = current_agg.get("valueField2") or current_agg.get("valueField") or "count"
            value_field2_alias = process_column_reference(
                value_field2,
                database_type,
                None,
                False,
                True
            )
            
            value_field2_type = current_agg.get("valueField2Type") or current_agg.get("valueFieldType")
            value2_expr = ""
            if value_field2_type == "bool":
                value2_expr = f"CASE WHEN {value_field2_alias} THEN 1 ELSE 0 END"
            else:
                value2_expr = value_field2_alias
            
            value2_alias_substring = ""
            if current_agg.get("valueField2") and current_agg.get("valueField") != current_agg.get("valueField2"):
                value2_alias_substring = f"{process_column_reference(current_agg['valueField2'], database_type, None, True)} AS {value_field2_alias}"
            
            # Percentage with same field for numerator and denominator
            if current_agg.get("valueField") == current_agg.get("valueField2") or not current_agg.get("valueField2"):
                for column in filtered_values:
                    case_when_columns.append(
                        f"CAST(sum(CASE WHEN {column_field_alias} = '{process_single_quotes(column, database_type)}' THEN {value_expr} END) AS FLOAT) / GREATEST(sum({value2_expr}), 1) AS {process_column_reference(column + disambiguation, database_type, '_', True)}"
                    )
            else:
                # Percentage with different fields
                for column in filtered_values:
                    case_when_columns.append(
                        f"CAST(sum(CASE WHEN {column_field_alias} = '{process_single_quotes(column, database_type)}' THEN {value_expr} END) AS FLOAT) / GREATEST(sum(CASE WHEN {column_field_alias} = '{process_single_quotes(column, database_type)}' THEN {value2_expr} END), 1) AS {process_column_reference(column + disambiguation, database_type, '_', True)}"
                    )
                if value2_alias_substring:
                    column_aliases.append(value2_alias_substring)
        else:
            # Standard aggregations (sum, count, avg, min, max)
            for column in filtered_values:
                case_when_columns.append(
                    f"{process_agg_type(agg_type, True)}(CASE WHEN {column_field_alias} = '{process_single_quotes(column, database_type)}' THEN {value_expr} END) AS {process_column_reference(column + disambiguation, database_type, '_', True)}"
                )
        
        if value_alias_substring:
            column_aliases.append(value_alias_substring)
    
    # Add the column field to the aliases
    column_aliases.append(
        f"{process_column_reference(column_field, database_type, None, True)} AS {column_field_alias}"
    )
    
    # Remove duplicates
    unique_column_aliases = list(dict.fromkeys(column_aliases))
    
    # Replace markers with actual SQL
    hydrated_template = template.replace(
        PIVOT_COLUMN_ALIAS_MARKER,
        ", ".join(unique_column_aliases)
    ).replace(
        PIVOT_COLUMN_MARKER,
        ", ".join(case_when_columns)
    )
    
    return hydrated_template


# ============================================================================
# VALIDATION
# ============================================================================


def validate_template(template: str, config: PivotConfig) -> Dict[str, Any]:
    """Validates that a template can be hydrated with the given config."""
    errors = []
    
    if not template:
        errors.append("Template is empty")
    
    if config.get("requiresDistinctValues"):
        if PIVOT_COLUMN_MARKER not in template:
            errors.append(f"Template is missing {PIVOT_COLUMN_MARKER} marker")
        if PIVOT_COLUMN_ALIAS_MARKER not in template:
            errors.append(f"Template is missing {PIVOT_COLUMN_ALIAS_MARKER} marker")
        if not config.get("columnField"):
            errors.append("config is missing columnField")
        if not config.get("rowField"):
            errors.append("config is missing rowField")
    
    if not config.get("aggregations") or len(config.get("aggregations", [])) == 0:
        errors.append("config is missing aggregations")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


