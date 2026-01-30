from enum import Enum
from typing import Union, Any, Optional
from dataclasses import dataclass, asdict

# Constants
IS_EXACTLY = 'is exactly'
IS_NOT_EXACTLY = 'is not exactly'
CONTAINS = 'contains'
IS = 'is'
IS_NOT = 'is not'
IS_NOT_NULL = 'is not null'
IS_NULL = 'is null'

IN_THE_LAST = 'in the last'
IN_THE_PREVIOUS = 'in the previous'
IN_THE_CURRENT = 'in the current'

EQUAL_TO = 'equal to'
NOT_EQUAL_TO = 'not equal to'
GREATER_THAN = 'greater than'
LESS_THAN = 'less than'
GREATER_THAN_OR_EQUAL_TO = 'greater than or equal to'
LESS_THAN_OR_EQUAL_TO = 'less than or equal to'

YEAR = 'year'
QUARTER = 'quarter'
MONTH = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'

NUMBER = 'number'
STRING = 'string'
DATE = 'date'
NULL = 'null'
CUSTOM = 'custom'
BOOLEAN = 'boolean'

# Enums
class StringOperator(Enum):
    IS_EXACTLY = IS_EXACTLY
    IS_NOT_EXACTLY = IS_NOT_EXACTLY
    CONTAINS = CONTAINS
    IS = IS
    IS_NOT = IS_NOT

class DateOperator(Enum):
    CUSTOM = CUSTOM
    IN_THE_LAST = IN_THE_LAST
    IN_THE_PREVIOUS = IN_THE_PREVIOUS
    IN_THE_CURRENT = IN_THE_CURRENT
    EQUAL_TO = EQUAL_TO
    NOT_EQUAL_TO = NOT_EQUAL_TO
    GREATER_THAN = GREATER_THAN
    LESS_THAN = LESS_THAN
    GREATER_THAN_OR_EQUAL_TO = GREATER_THAN_OR_EQUAL_TO
    LESS_THAN_OR_EQUAL_TO = LESS_THAN_OR_EQUAL_TO

class NumberOperator(Enum):
    EQUAL_TO = EQUAL_TO
    NOT_EQUAL_TO = NOT_EQUAL_TO
    GREATER_THAN = GREATER_THAN
    LESS_THAN = LESS_THAN
    GREATER_THAN_OR_EQUAL_TO = GREATER_THAN_OR_EQUAL_TO
    LESS_THAN_OR_EQUAL_TO = LESS_THAN_OR_EQUAL_TO

class NullOperator(Enum):
    IS_NOT_NULL = IS_NOT_NULL
    IS_NULL = IS_NULL

class BoolOperator(Enum):
    EQUAL_TO = EQUAL_TO
    NOT_EQUAL_TO = NOT_EQUAL_TO

class TimeUnit(Enum):
    YEAR = YEAR
    QUARTER = QUARTER
    MONTH = MONTH
    WEEK = WEEK
    DAY = DAY
    HOUR = HOUR

class FieldType(Enum):
    STRING = STRING
    NUMBER = NUMBER
    DATE = DATE
    NULL = NULL
    BOOLEAN = BOOLEAN

class FilterType(Enum):
    STRING_FILTER = 'string-filter'
    DATE_FILTER = 'date-filter'
    DATE_CUSTOM_FILTER = 'date-custom-filter'
    DATE_COMPARISON_FILTER = 'date-comparison-filter'
    NUMERIC_FILTER = 'numeric-filter'
    NULL_FILTER = 'null-filter'
    STRING_IN_FILTER = 'string-in-filter'
    BOOLEAN_FILTER = 'boolean-filter'

# Types
Operator = Union[StringOperator, DateOperator, NumberOperator, NullOperator, BoolOperator]

# Base Filter Interface
@dataclass
class DateRange:
    startDate: str
    endDate: str

@dataclass
class DateValue:
    value: int
    unit: TimeUnit
@dataclass
class BaseFilter:
    filterType: FilterType
    fieldType: FieldType
    operator: Operator
    field: str
    value: Union[bool, int, str, list[str], DateRange, DateValue, None]
    table: Optional[str] = None

@dataclass
class Filter:
    filter_type: FilterType
    operator: Operator
    value: Union[bool, int, str, list[str], DateRange, DateValue, None]
    field: str
    table: str

def convert_custom_filter(filter: Filter) -> dict:
    if filter.filter_type == FilterType.STRING_FILTER:
        if not isinstance(filter.value, str):
            raise ValueError('Invalid value for StringFilter, expected string')
        if filter.operator not in StringOperator:
            raise ValueError('Invalid operator for StringFilter, expected StringOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.STRING, filter.operator, filter.field, filter.value, filter.table)) 
    elif filter.filter_type == FilterType.STRING_IN_FILTER:
        if not isinstance(filter.value, list):
            raise ValueError('Invalid value for StringInFilter, expected list')
        if filter.operator not in StringOperator:
            raise ValueError('Invalid operator for StringInFilter, expected StringOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.STRING, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.NUMERIC_FILTER:
        if not isinstance(filter.value, int):
            raise ValueError('Invalid value for NumericFilter, expected int')
        if filter.operator not in NumberOperator:
            raise ValueError('Invalid operator for NumericFilter, expected NumberOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.NUMBER, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.DATE_FILTER:
        if not isinstance(filter.value, DateValue) or filter.value is None:
            raise ValueError('Invalid value for DateFilter, expected DateValue')
        if filter.operator not in DateOperator:
            raise ValueError('Invalid operator for DateFilter, expected DateOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.DATE, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.DATE_CUSTOM_FILTER:
        if not isinstance(filter.value, DateRange) or filter.value is None:
            raise ValueError('Invalid value for DateCustomFilter, expected DateRange')
        if filter.operator not in DateOperator:
            raise ValueError('Invalid operator for DateCustomFilter, expected DateOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.DATE, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.DATE_COMPARISON_FILTER:
        if not isinstance(filter.value, str):
            raise ValueError('Invalid value for DateComparisonFilter, expected str')
        if filter.operator not in DateOperator:
            raise ValueError('Invalid operator for DateComparisonFilter, expected DateOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.DATE, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.NULL_FILTER:
        if filter.value is not None:
            raise ValueError('Invalid value for NullFilter, expected None')
        if filter.operator not in NullOperator:
            raise ValueError('Invalid operator for NullFilter, expected NullOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.NULL, filter.operator, filter.field, filter.value, filter.table))
    elif filter.filter_type == FilterType.BOOLEAN_FILTER:
        if not isinstance(filter.value, bool):
            raise ValueError('Invalid value for BooleanFilter, expected bool')
        if filter.operator not in BoolOperator:
            raise ValueError('Invalid operator for BooleanFilter, expected BoolOperator')
        return asdict(BaseFilter(filter.filter_type, FieldType.BOOLEAN, filter.operator, filter.field, filter.value, filter.table))
    else:
        raise ValueError(f'Unknown filter type: {filter.filter_type}')