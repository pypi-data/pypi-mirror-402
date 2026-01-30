"""Tests for error handling

This module contains tests for error handling in security-related operations.
"""

from unittest.mock import AsyncMock, patch

import pytest

from mcp_server.database.query_executor import QueryExecutor, QueryResult
from mcp_server.utils.errors import DatabaseError, ErrorCode, SecurityError


class TestSecurityErrorTypes:
    """Tests for different security error types"""

    def test_select_only_error(self):
        """Test SELECT_ONLY error code and message"""
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety("INSERT INTO view.Contract VALUES (1)")

        error = exc_info.value
        assert error.code == ErrorCode.SELECT_ONLY
        assert "SELECT" in error.message

    def test_dangerous_sql_error(self):
        """Test DANGEROUS_SQL error code"""
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety("SELECT * FROM view.Contract; DROP TABLE x")

        error = exc_info.value
        assert error.code == ErrorCode.DANGEROUS_SQL
        assert "DROP" in error.message

    def test_unauthorized_table_error(self):
        """Test UNAUTHORIZED_TABLE error code"""
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_tables("SELECT * FROM dbo.SomeTable")

        error = exc_info.value
        assert error.code == ErrorCode.UNAUTHORIZED_TABLE
        assert "dbo.SomeTable" in error.message

    def test_sql_comment_error(self):
        """Test SQL_COMMENT_NOT_ALLOWED error code"""
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety("SELECT * FROM view.Contract -- comment")

        error = exc_info.value
        assert error.code == ErrorCode.SQL_COMMENT_NOT_ALLOWED


class TestSecurityErrorProperties:
    """Tests for SecurityError class properties"""

    def test_security_error_has_sql_context(self):
        """Test that SecurityError includes SQL context in details"""
        try:
            QueryExecutor.validate_sql_safety("DELETE FROM view.Contract WHERE Id = 1")
        except SecurityError as e:
            # Error should include truncated SQL in details dict
            assert "sql" in e.details and e.details["sql"] is not None

    def test_security_error_string_representation(self):
        """Test SecurityError string representation"""
        error = SecurityError(ErrorCode.SELECT_ONLY, "Only SELECT allowed", sql="DELETE...")
        error_str = str(error)
        assert "SELECT" in error_str or error.message in error_str


class TestErrorRecovery:
    """Tests for error recovery scenarios"""

    @pytest.mark.asyncio
    async def test_security_error_does_not_affect_subsequent_queries(self):
        """Test that a security error doesn't break subsequent valid queries"""
        # First, trigger a security error
        with pytest.raises(SecurityError):
            QueryExecutor.validate_sql_safety("DELETE FROM view.Contract")

        # Then verify a valid query still works
        QueryExecutor.validate_sql_safety("SELECT * FROM view.Contract")
        QueryExecutor.validate_tables("SELECT * FROM view.Contract")

    @pytest.mark.asyncio
    async def test_executor_state_after_failed_query(self):
        """Test that executor state is clean after failed query"""
        with (
            patch("mcp_server.database.query_executor.DatabasePool") as mock_pool,
            patch("mcp_server.database.query_executor.log_query"),
        ):
            mock_pool.execute_query = AsyncMock(side_effect=Exception("DB Error"))

            # First query fails
            with pytest.raises(Exception):
                await QueryExecutor.execute(
                    sql="SELECT * FROM view.Contract",
                    purpose="First query",
                )

            # Reset mock for successful second query
            mock_pool.execute_query = AsyncMock(return_value=(["Id"], [[1]]))

            # Second query should succeed
            result = await QueryExecutor.execute(
                sql="SELECT * FROM view.Contract",
                purpose="Second query",
            )
            assert result.success


class TestErrorCodeCoverage:
    """Tests to ensure all error codes are properly used"""

    def test_error_code_enum_values(self):
        """Test that ErrorCode enum has expected values"""
        expected_codes = [
            "SELECT_ONLY",
            "DANGEROUS_SQL",
            "UNAUTHORIZED_TABLE",
            "SQL_COMMENT_NOT_ALLOWED",
        ]

        for code_name in expected_codes:
            assert hasattr(ErrorCode, code_name), f"Missing ErrorCode: {code_name}"


class TestGracefulDegradation:
    """Tests for graceful degradation under error conditions"""

    @pytest.mark.asyncio
    async def test_database_connection_error_handling(self):
        """Test handling of database connection errors"""
        with (
            patch("mcp_server.database.query_executor.DatabasePool") as mock_pool,
            patch("mcp_server.database.query_executor.log_query"),
        ):
            mock_pool.execute_query = AsyncMock(
                side_effect=Exception("Connection refused")
            )

            with pytest.raises(Exception) as exc_info:
                await QueryExecutor.execute(
                    sql="SELECT * FROM view.Contract",
                    purpose="Test query",
                )

            assert "Connection" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_timeout_handling(self):
        """Test handling of query timeout"""
        with (
            patch("mcp_server.database.query_executor.DatabasePool") as mock_pool,
            patch("mcp_server.database.query_executor.log_query"),
        ):
            mock_pool.execute_query = AsyncMock(
                side_effect=TimeoutError("Query timeout after 30 seconds")
            )

            with pytest.raises(TimeoutError):
                await QueryExecutor.execute(
                    sql="SELECT * FROM view.Contract",
                    purpose="Slow query",
                )


class TestToolErrorResponse:
    """Tests for query_database tool error responses"""

    @pytest.mark.asyncio
    async def test_tool_returns_error_response_for_security_error(self):
        """Test that tool returns proper error response for security errors"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            side_effect=SecurityError(
                ErrorCode.SELECT_ONLY, "Only SELECT statements are allowed"
            ),
        ):
            result = await query_tool.fn(
                sql="DELETE FROM view.Contract",
                purpose="Test",
            )

            assert result["success"] is False
            assert result["row_count"] == 0
            assert result["columns"] == []
            assert result["rows"] == []
            assert "安全錯誤" in result["message"]

    @pytest.mark.asyncio
    async def test_tool_returns_error_response_for_database_error(self):
        """Test that tool returns proper error response for database errors"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            side_effect=DatabaseError(
                ErrorCode.DB_QUERY_ERROR, "Connection failed"
            ),
        ):
            result = await query_tool.fn(
                sql="SELECT * FROM view.Contract",
                purpose="Test",
            )

            assert result["success"] is False
            assert "資料庫錯誤" in result["message"]

    @pytest.mark.asyncio
    async def test_tool_returns_error_response_for_unexpected_error(self):
        """Test that tool handles unexpected errors gracefully"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Unexpected internal error"),
        ):
            result = await query_tool.fn(
                sql="SELECT * FROM view.Contract",
                purpose="Test",
            )

            assert result["success"] is False
            assert "查詢錯誤" in result["message"]
            # Should not expose internal error details excessively
            assert "Unexpected internal error" in result["message"]


class TestErrorMessageLocalization:
    """Tests for error message localization (Chinese)"""

    @pytest.mark.asyncio
    async def test_error_messages_in_chinese(self):
        """Test that user-facing error messages are in Chinese"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        error_scenarios = [
            (
                SecurityError(ErrorCode.SELECT_ONLY, "Only SELECT allowed"),
                "安全錯誤",
            ),
            (
                DatabaseError(ErrorCode.DB_QUERY_ERROR, "DB error"),
                "資料庫錯誤",
            ),
            (
                Exception("Unknown error"),
                "查詢錯誤",
            ),
        ]

        for error, expected_prefix in error_scenarios:
            with patch(
                "mcp_server.tools.query.QueryExecutor.execute",
                new_callable=AsyncMock,
                side_effect=error,
            ):
                result = await query_tool.fn(
                    sql="SELECT * FROM view.Contract",
                    purpose="Test",
                )

                assert expected_prefix in result["message"], (
                    f"Expected '{expected_prefix}' in message for {type(error).__name__}"
                )
