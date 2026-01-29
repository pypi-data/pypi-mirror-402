"""Filter matching utility module for dictionary records.

This module provides filtering capabilities using mistql for evaluating
boolean filter expressions on dictionary records. It replaces dictquery
functionality with a mistql-based implementation.
"""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def match_filter(record: dict[str, Any], filter_expr: Optional[str]) -> bool:
    """Match a record against a filter expression.

    This function evaluates a boolean filter expression against a dictionary
    record using mistql. Returns True if the record matches the filter,
    False otherwise.

    Args:
        record: Dictionary record to evaluate
        filter_expr: Filter expression string (e.g., "age >= 18", "status == 'active'")
                    If None, returns True (no filter applied)

    Returns:
        True if record matches the filter, False otherwise

    Raises:
        ValueError: If filter expression is invalid
        Exception: Re-raises any mistql evaluation errors with context
    """
    if filter_expr is None:
        return True

    if not isinstance(record, dict):
        logger.warning('match_filter: record is not a dict, returning False')
        return False

    try:
        from mistql import query

        # mistql can evaluate boolean expressions directly
        # For filtering, we need to check if the expression evaluates to true
        # mistql query format: wrap record and check expression result
        # Use mistql's filter syntax: [record] | filter <expression>
        # If the filtered array has items, the expression matches

        # Wrap single record in array for mistql filter
        data = [record]
        mistql_query = f'filter {filter_expr}'

        # Execute mistql query (returns filtered array)
        result = query(mistql_query, data)

        # Check if filter returned any results (i.e., expression matched)
        if isinstance(result, list):
            return len(result) > 0
        # If result is truthy but not a list, expression evaluated to truthy value
        return bool(result)

    except ImportError as e:
        logger.error('mistql is not available: %s', e)
        raise RuntimeError('mistql library is required for filtering') from e
    except Exception as e:
        logger.debug('Filter evaluation error: %s, expression: %s, record: %s', e, filter_expr, record)
        # Re-raise with more context
        raise ValueError(f'Invalid filter expression "{filter_expr}": {e}') from e


def translate_filter_to_sql(filter_expr: Optional[str]) -> Optional[str]:
    """Translate basic filter expression to SQL WHERE clause.

    This function provides basic translation of filter expressions to SQL
    WHERE clauses for use with DuckDB. It supports common comparison and
    logical operators.

    Args:
        filter_expr: Filter expression string (e.g., "age >= 18")
                    If None, returns None

    Returns:
        SQL WHERE clause string (without WHERE keyword) or None if translation
        not possible or not needed

    Note:
        This is a basic implementation. Complex expressions may not be
        translatable and should use the iterable engine with match_filter()
        instead.
    """
    if filter_expr is None:
        return None

    # Basic SQL translation for simple expressions
    # This handles common cases but is not comprehensive
    # For complex expressions, fall back to iterable engine filtering

    # For now, return None to indicate translation not implemented
    # This can be enhanced later based on actual usage patterns
    logger.debug('translate_filter_to_sql: basic translation not yet implemented for: %s', filter_expr)
    return None
