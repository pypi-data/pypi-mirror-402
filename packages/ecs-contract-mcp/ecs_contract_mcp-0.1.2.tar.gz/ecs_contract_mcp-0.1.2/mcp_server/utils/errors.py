"""Error definitions and exception classes"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Error codes for the MCP Server"""

    # Validation errors
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # Permission errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHORIZED = "UNAUTHORIZED"

    # Security errors (SQL validation)
    SECURITY_VIOLATION = "SECURITY_VIOLATION"
    UNAUTHORIZED_TABLE = "UNAUTHORIZED_TABLE"
    DANGEROUS_SQL = "DANGEROUS_SQL"
    SQL_COMMENT_NOT_ALLOWED = "SQL_COMMENT_NOT_ALLOWED"
    SELECT_ONLY = "SELECT_ONLY"

    # Database errors
    DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
    DB_QUERY_ERROR = "DB_QUERY_ERROR"
    DB_TIMEOUT = "DB_TIMEOUT"

    # Data errors
    NOT_FOUND = "NOT_FOUND"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"

    # System errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ToolError(Exception):
    """Base exception for tool errors"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details,
        }


class SecurityError(ToolError):
    """Security validation exception (SQL validation failures)"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        sql: str | None = None,
    ):
        details = {"sql": sql} if sql else {}
        super().__init__(code, message, details)


class DatabaseError(ToolError):
    """Database operation exception"""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        original_error: Exception | None = None,
    ):
        details = {"original_error": str(original_error)} if original_error else {}
        super().__init__(code, message, details)
        self.original_error = original_error
