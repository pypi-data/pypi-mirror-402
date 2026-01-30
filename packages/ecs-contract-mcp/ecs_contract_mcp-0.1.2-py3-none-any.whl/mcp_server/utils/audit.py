"""Audit logging for query tracking"""

from mcp_server.utils.logging import get_logger

# Dedicated audit logger
audit_logger = get_logger("audit")


def log_query(
    sql: str,
    purpose: str,
    row_count: int,
    execution_time_ms: int,
    success: bool,
    error: str | None = None,
) -> None:
    """Log a query execution for audit purposes

    Args:
        sql: The SQL query that was executed
        purpose: The stated purpose of the query
        row_count: Number of rows returned
        execution_time_ms: Query execution time in milliseconds
        success: Whether the query succeeded
        error: Error message if the query failed
    """
    audit_logger.info(
        "query_executed",
        sql=sql,
        purpose=purpose,
        row_count=row_count,
        execution_time_ms=execution_time_ms,
        success=success,
        error=error,
    )


def log_security_violation(
    sql: str,
    violation_type: str,
    details: str,
) -> None:
    """Log a security violation attempt

    Args:
        sql: The SQL query that was rejected
        violation_type: Type of security violation
        details: Details about the violation
    """
    audit_logger.warning(
        "security_violation",
        sql=sql,
        violation_type=violation_type,
        details=details,
    )
