"""Secure query executor with SQL validation and whitelist enforcement"""

import re
import time
from dataclasses import dataclass
from typing import Any

from mcp_server.config import settings
from mcp_server.database.allowed_views import is_view_allowed, normalize_table_name
from mcp_server.database.connection import DatabasePool
from mcp_server.utils.audit import log_query, log_security_violation
from mcp_server.utils.errors import ErrorCode, SecurityError
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)

# Dangerous SQL keywords that are not allowed
DANGEROUS_KEYWORDS: list[str] = [
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "EXEC",
    "EXECUTE",
    "sp_",
    "xp_",
    "GRANT",
    "REVOKE",
    "DENY",
    "BACKUP",
    "RESTORE",
    "SHUTDOWN",
    "DBCC",
    "BULK",
    "OPENROWSET",
    "OPENDATASOURCE",
    "INTO",  # SELECT INTO
]


@dataclass
class QueryResult:
    """Result of a query execution"""

    success: bool
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    execution_time_ms: int
    message: str | None = None


class QueryExecutor:
    """Secure query executor with validation and auditing"""

    @staticmethod
    def extract_tables_from_sql(sql: str) -> list[str]:
        """Extract table/view names from SQL query

        Handles both formats:
        - FROM view.Contract
        - FROM [view].[Contract]

        Args:
            sql: The SQL query

        Returns:
            List of table/view names found in the query (normalized without brackets)
        """
        tables = []

        # Pattern 1: [schema].[table] format
        bracket_pattern = r"\b(?:FROM|JOIN)\s+\[([^\]]+)\]\.\[([^\]]+)\]"
        bracket_matches = re.findall(bracket_pattern, sql, re.IGNORECASE)
        for schema, table in bracket_matches:
            tables.append(f"{schema}.{table}")

        # Pattern 2: schema.table format (without brackets)
        simple_pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)"
        simple_matches = re.findall(simple_pattern, sql, re.IGNORECASE)
        tables.extend(simple_matches)

        # Normalize all table names
        normalized = [normalize_table_name(t) for t in tables]
        return list(set(normalized))

    @staticmethod
    def validate_sql_safety(sql: str) -> None:
        """Validate SQL query for safety

        Args:
            sql: The SQL query to validate

        Raises:
            SecurityError: If the SQL is not safe
        """
        sql_upper = sql.upper().strip()

        # 1. Only allow SELECT statements
        if not sql_upper.startswith("SELECT"):
            log_security_violation(sql, "SELECT_ONLY", "Query does not start with SELECT")
            raise SecurityError(
                ErrorCode.SELECT_ONLY,
                "Only SELECT statements are allowed",
                sql=sql[:200],
            )

        # 2. Check for dangerous keywords
        for keyword in DANGEROUS_KEYWORDS:
            # Use word boundary to avoid false positives
            pattern = rf"\b{keyword}\b"
            if re.search(pattern, sql_upper):
                log_security_violation(sql, "DANGEROUS_SQL", f"Contains keyword: {keyword}")
                raise SecurityError(
                    ErrorCode.DANGEROUS_SQL,
                    f"Dangerous keyword '{keyword}' is not allowed",
                    sql=sql[:200],
                )

        # 3. Check for SQL comments (could be used to bypass checks)
        if "--" in sql or "/*" in sql:
            log_security_violation(sql, "SQL_COMMENT", "SQL contains comments")
            raise SecurityError(
                ErrorCode.SQL_COMMENT_NOT_ALLOWED,
                "SQL comments are not allowed",
                sql=sql[:200],
            )

    @staticmethod
    def validate_tables(sql: str) -> None:
        """Validate that all tables in the query are in the whitelist

        Args:
            sql: The SQL query to validate

        Raises:
            SecurityError: If any table is not in the whitelist
        """
        tables = QueryExecutor.extract_tables_from_sql(sql)

        for table in tables:
            if not is_view_allowed(table):
                log_security_violation(
                    sql, "UNAUTHORIZED_TABLE", f"Attempted to query: {table}"
                )
                raise SecurityError(
                    ErrorCode.UNAUTHORIZED_TABLE,
                    f"Table/View '{table}' is not allowed. Only views in the 'view' schema are permitted.",
                    sql=sql[:200],
                )

    @staticmethod
    def enforce_row_limit(sql: str, max_rows: int | None = None) -> str:
        """Add TOP clause to limit result rows if not already present

        Args:
            sql: The SQL query
            max_rows: Maximum rows to return (default: settings.MAX_ROWS)

        Returns:
            SQL with TOP clause added if needed
        """
        max_rows = max_rows or settings.MAX_ROWS
        sql_upper = sql.upper()

        # Check if TOP is already present
        if "TOP" in sql_upper:
            return sql

        # Add TOP after SELECT (handle SELECT DISTINCT too)
        sql = re.sub(
            r"^(SELECT\s+(?:DISTINCT\s+)?)",
            rf"\1TOP {max_rows} ",
            sql,
            count=1,
            flags=re.IGNORECASE,
        )
        return sql

    @classmethod
    async def execute(
        cls,
        sql: str,
        purpose: str,
        max_rows: int | None = None,
    ) -> QueryResult:
        """Execute a query with full validation and auditing

        Args:
            sql: The SQL query to execute
            purpose: The stated purpose of the query (for audit)
            max_rows: Maximum rows to return

        Returns:
            QueryResult with the query results

        Raises:
            SecurityError: If the query fails validation
            DatabaseError: If the query execution fails
        """
        max_rows = max_rows or settings.MAX_ROWS
        start_time = time.time()

        try:
            # Validate SQL safety
            cls.validate_sql_safety(sql)

            # Validate tables are in whitelist
            cls.validate_tables(sql)

            # Enforce row limit
            limited_sql = cls.enforce_row_limit(sql, max_rows)

            # Execute the query
            columns, rows = await DatabasePool.execute_query(limited_sql)

            # Calculate execution time
            execution_time_ms = int((time.time() - start_time) * 1000)

            # Check if results were truncated
            truncated = len(rows) >= max_rows

            # Log the query for audit
            log_query(
                sql=sql,
                purpose=purpose,
                row_count=len(rows),
                execution_time_ms=execution_time_ms,
                success=True,
            )

            return QueryResult(
                success=True,
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
                execution_time_ms=execution_time_ms,
            )

        except SecurityError:
            # Re-raise security errors
            raise

        except Exception as e:
            # Log failed queries
            execution_time_ms = int((time.time() - start_time) * 1000)
            log_query(
                sql=sql,
                purpose=purpose,
                row_count=0,
                execution_time_ms=execution_time_ms,
                success=False,
                error=str(e),
            )
            raise
