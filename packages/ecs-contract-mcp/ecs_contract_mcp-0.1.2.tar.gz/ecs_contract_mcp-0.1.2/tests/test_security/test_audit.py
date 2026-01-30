"""Tests for audit logging

This module contains tests for audit log completeness and correctness.
"""

from unittest.mock import MagicMock, patch

import pytest

from mcp_server.utils.audit import log_query, log_security_violation


class TestLogQuery:
    """Tests for query audit logging"""

    def test_log_query_success(self):
        """Test logging successful query"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract",
                purpose="Test query",
                row_count=100,
                execution_time_ms=50,
                success=True,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[0][0] == "query_executed"
            assert call_args[1]["sql"] == "SELECT * FROM view.Contract"
            assert call_args[1]["purpose"] == "Test query"
            assert call_args[1]["row_count"] == 100
            assert call_args[1]["execution_time_ms"] == 50
            assert call_args[1]["success"] is True
            assert call_args[1]["error"] is None

    def test_log_query_failure(self):
        """Test logging failed query"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract",
                purpose="Test query",
                row_count=0,
                execution_time_ms=10,
                success=False,
                error="Connection timeout",
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert call_args[1]["success"] is False
            assert call_args[1]["error"] == "Connection timeout"

    def test_log_query_with_large_sql(self):
        """Test logging query with large SQL"""
        large_sql = "SELECT * FROM view.Contract WHERE " + " OR ".join(
            [f"Id = {i}" for i in range(1000)]
        )
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql=large_sql,
                purpose="Large query test",
                row_count=1000,
                execution_time_ms=500,
                success=True,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            # Full SQL should be logged
            assert large_sql in call_args[1]["sql"]

    def test_log_query_with_special_characters(self):
        """Test logging query with special characters in purpose"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract WHERE Title LIKE '%測試%'",
                purpose="查詢包含「測試」的合約",
                row_count=5,
                execution_time_ms=20,
                success=True,
            )

            mock_logger.info.assert_called_once()
            call_args = mock_logger.info.call_args
            assert "測試" in call_args[1]["purpose"]


class TestLogSecurityViolation:
    """Tests for security violation logging"""

    def test_log_security_violation(self):
        """Test logging security violation"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_security_violation(
                sql="DELETE FROM view.Contract",
                violation_type="SELECT_ONLY",
                details="Query does not start with SELECT",
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[0][0] == "security_violation"
            assert call_args[1]["sql"] == "DELETE FROM view.Contract"
            assert call_args[1]["violation_type"] == "SELECT_ONLY"
            assert "Query does not start with SELECT" in call_args[1]["details"]

    def test_log_unauthorized_table_violation(self):
        """Test logging unauthorized table access attempt"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_security_violation(
                sql="SELECT * FROM dbo.SensitiveData",
                violation_type="UNAUTHORIZED_TABLE",
                details="Attempted to query: dbo.SensitiveData",
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["violation_type"] == "UNAUTHORIZED_TABLE"

    def test_log_dangerous_sql_violation(self):
        """Test logging dangerous SQL keyword violation"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_security_violation(
                sql="SELECT * FROM view.Contract; DROP TABLE view.Contract",
                violation_type="DANGEROUS_SQL",
                details="Contains keyword: DROP",
            )

            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert call_args[1]["violation_type"] == "DANGEROUS_SQL"
            assert "DROP" in call_args[1]["details"]


class TestAuditIntegrationWithQueryExecutor:
    """Tests for audit logging integration with QueryExecutor"""

    @pytest.mark.asyncio
    async def test_successful_query_logged(self):
        """Test that successful query execution is logged"""
        from unittest.mock import AsyncMock

        from mcp_server.database.query_executor import QueryExecutor

        with (
            patch("mcp_server.database.query_executor.DatabasePool") as mock_pool,
            patch("mcp_server.database.query_executor.log_query") as mock_log,
        ):
            mock_pool.execute_query = AsyncMock(
                return_value=(["ContractId", "Title"], [[1, "Test"]])
            )

            await QueryExecutor.execute(
                sql="SELECT ContractId, Title FROM view.Contract",
                purpose="Test query",
            )

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["success"] is True
            assert call_args[1]["row_count"] == 1

    @pytest.mark.asyncio
    async def test_failed_query_logged(self):
        """Test that failed query execution is logged"""
        from unittest.mock import AsyncMock

        from mcp_server.database.query_executor import QueryExecutor

        with (
            patch("mcp_server.database.query_executor.DatabasePool") as mock_pool,
            patch("mcp_server.database.query_executor.log_query") as mock_log,
        ):
            mock_pool.execute_query = AsyncMock(
                side_effect=Exception("Database connection error")
            )

            with pytest.raises(Exception):
                await QueryExecutor.execute(
                    sql="SELECT * FROM view.Contract",
                    purpose="Test query",
                )

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[1]["success"] is False
            assert "Database connection error" in call_args[1]["error"]

    def test_security_violation_logged(self):
        """Test that security violations are logged"""
        from mcp_server.database.query_executor import QueryExecutor
        from mcp_server.utils.errors import SecurityError

        with patch(
            "mcp_server.database.query_executor.log_security_violation"
        ) as mock_log:
            with pytest.raises(SecurityError):
                QueryExecutor.validate_sql_safety("DELETE FROM view.Contract")

            mock_log.assert_called_once()
            # Check positional arguments: (sql, violation_type, details)
            call_args = mock_log.call_args
            assert call_args[0][1] == "SELECT_ONLY"  # violation_type is 2nd arg


class TestAuditLogFields:
    """Tests to verify all required audit fields are captured"""

    def test_query_log_has_all_required_fields(self):
        """Test that query log includes all required fields"""
        required_fields = [
            "sql",
            "purpose",
            "row_count",
            "execution_time_ms",
            "success",
            "error",
        ]

        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract",
                purpose="Test",
                row_count=0,
                execution_time_ms=0,
                success=True,
                error=None,
            )

            call_args = mock_logger.info.call_args
            for field in required_fields:
                assert field in call_args[1], f"Missing required field: {field}"

    def test_security_log_has_all_required_fields(self):
        """Test that security violation log includes all required fields"""
        required_fields = ["sql", "violation_type", "details"]

        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_security_violation(
                sql="DELETE FROM view.Contract",
                violation_type="SELECT_ONLY",
                details="Not allowed",
            )

            call_args = mock_logger.warning.call_args
            for field in required_fields:
                assert field in call_args[1], f"Missing required field: {field}"


class TestAuditLogLevels:
    """Tests for appropriate log levels"""

    def test_successful_query_uses_info_level(self):
        """Test that successful queries use INFO level"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract",
                purpose="Test",
                row_count=10,
                execution_time_ms=50,
                success=True,
            )

            mock_logger.info.assert_called_once()
            mock_logger.warning.assert_not_called()
            mock_logger.error.assert_not_called()

    def test_failed_query_uses_info_level(self):
        """Test that failed queries still use INFO level (not error)"""
        # Failed queries are logged at info level because failure might be due to
        # user error (bad SQL syntax) rather than system error
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_query(
                sql="SELECT * FROM view.Contract",
                purpose="Test",
                row_count=0,
                execution_time_ms=10,
                success=False,
                error="Syntax error",
            )

            mock_logger.info.assert_called_once()

    def test_security_violation_uses_warning_level(self):
        """Test that security violations use WARNING level"""
        with patch("mcp_server.utils.audit.audit_logger") as mock_logger:
            log_security_violation(
                sql="DROP TABLE view.Contract",
                violation_type="SELECT_ONLY",
                details="Not a SELECT statement",
            )

            mock_logger.warning.assert_called_once()
            mock_logger.info.assert_not_called()
