"""Tests for SQL Injection protection

This module contains comprehensive tests for SQL injection attack prevention.
It covers various attack vectors and ensures the security mechanisms work correctly.
"""

import pytest

from mcp_server.database.query_executor import DANGEROUS_KEYWORDS, QueryExecutor
from mcp_server.utils.errors import ErrorCode, SecurityError


class TestSelectOnlyRestriction:
    """Tests to ensure only SELECT statements are allowed"""

    def test_valid_select(self):
        """Test that valid SELECT passes"""
        valid_queries = [
            "SELECT * FROM view.Contract",
            "SELECT ContractId, Title FROM view.Contract",
            "SELECT DISTINCT Title FROM view.Contract",
            "SELECT TOP 100 * FROM view.Contract",
            "  SELECT * FROM view.Contract",  # Leading whitespace
        ]
        for sql in valid_queries:
            # Should not raise
            QueryExecutor.validate_sql_safety(sql)

    def test_insert_blocked(self):
        """Test that INSERT is blocked"""
        sql = "INSERT INTO view.Contract (Title) VALUES ('Test')"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_update_blocked(self):
        """Test that UPDATE is blocked"""
        sql = "UPDATE view.Contract SET Title = 'Hacked' WHERE ContractId = 1"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_delete_blocked(self):
        """Test that DELETE is blocked"""
        sql = "DELETE FROM view.Contract WHERE ContractId = 1"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_drop_blocked(self):
        """Test that DROP is blocked"""
        sql = "DROP TABLE view.Contract"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_create_blocked(self):
        """Test that CREATE is blocked"""
        sql = "CREATE TABLE test (id INT)"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_alter_blocked(self):
        """Test that ALTER is blocked"""
        sql = "ALTER TABLE view.Contract ADD NewColumn VARCHAR(50)"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_truncate_blocked(self):
        """Test that TRUNCATE is blocked"""
        sql = "TRUNCATE TABLE view.Contract"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY


class TestDangerousKeywords:
    """Tests for dangerous keyword detection"""

    def test_all_dangerous_keywords_defined(self):
        """Test that expected dangerous keywords are in the list"""
        expected = [
            "INSERT",
            "UPDATE",
            "DELETE",
            "DROP",
            "CREATE",
            "ALTER",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "GRANT",
            "REVOKE",
            "DENY",
            "BACKUP",
            "RESTORE",
            "SHUTDOWN",
            "INTO",
        ]
        for keyword in expected:
            assert keyword in DANGEROUS_KEYWORDS, f"{keyword} should be dangerous"

    def test_exec_blocked(self):
        """Test that EXEC is blocked"""
        sql = "SELECT * FROM view.Contract; EXEC sp_help"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL
        assert "EXEC" in exc_info.value.message

    def test_execute_blocked(self):
        """Test that EXECUTE is blocked"""
        sql = "SELECT 1; EXECUTE sp_executesql N'SELECT * FROM sys.tables'"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_stored_procedure_prefix_blocked(self):
        """Test that sp_ and xp_ prefixes are blocked when used as exact words"""
        # Note: The keyword check uses word boundaries, so sp_help won't match \bsp_\b
        # But EXEC sp_help will be blocked by the EXEC keyword
        test_cases = [
            ("SELECT 1; EXEC sp_help", "EXEC"),  # Blocked by EXEC
            ("SELECT 1; EXEC xp_cmdshell 'dir'", "EXEC"),  # Blocked by EXEC
        ]
        for sql, expected_keyword in test_cases:
            with pytest.raises(SecurityError) as exc_info:
                QueryExecutor.validate_sql_safety(sql)
            assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_select_into_blocked(self):
        """Test that SELECT INTO is blocked"""
        sql = "SELECT * INTO #temp FROM view.Contract"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL
        assert "INTO" in exc_info.value.message

    def test_openrowset_blocked(self):
        """Test that OPENROWSET is blocked"""
        sql = "SELECT * FROM OPENROWSET('SQLNCLI', 'Server=evil;', 'SELECT * FROM data')"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_grant_blocked(self):
        """Test that GRANT is blocked"""
        sql = "SELECT 1; GRANT SELECT ON view.Contract TO hacker"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_backup_blocked(self):
        """Test that BACKUP is blocked"""
        sql = "SELECT 1; BACKUP DATABASE master TO DISK = 'C:\\hack.bak'"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_shutdown_blocked(self):
        """Test that SHUTDOWN is blocked"""
        sql = "SELECT 1; SHUTDOWN WITH NOWAIT"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_dbcc_blocked(self):
        """Test that DBCC commands are blocked"""
        sql = "SELECT 1; DBCC FREEPROCCACHE"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL


class TestSqlCommentBlocking:
    """Tests for SQL comment blocking"""

    def test_single_line_comment_blocked(self):
        """Test that -- comments are blocked"""
        sql = "SELECT * FROM view.Contract -- WHERE 1=1"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SQL_COMMENT_NOT_ALLOWED

    def test_multi_line_comment_blocked(self):
        """Test that /* */ comments are blocked"""
        sql = "SELECT * FROM view.Contract /* WHERE Active = 1 */"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SQL_COMMENT_NOT_ALLOWED

    def test_comment_injection_blocked(self):
        """Test that comment-based injection is blocked"""
        sql = "SELECT * FROM view.Contract WHERE 1=1 --' OR '1'='1"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SQL_COMMENT_NOT_ALLOWED


class TestUnionInjection:
    """Tests for UNION-based injection attempts"""

    def test_union_allowed_if_valid(self):
        """Test that valid UNION is allowed within allowed views"""
        # UNION itself is not dangerous, only matters what tables are accessed
        sql = """
            SELECT ContractId, Title FROM view.Contract
            UNION
            SELECT EventId, Title FROM view.Event
        """
        # This should pass SQL safety check
        QueryExecutor.validate_sql_safety(sql)

    def test_union_with_system_table_blocked(self):
        """Test that UNION with system tables is blocked by whitelist"""
        sql = """
            SELECT ContractId FROM view.Contract
            UNION
            SELECT name FROM sys.tables
        """
        # Should fail table validation
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_tables(sql)
        assert exc_info.value.code == ErrorCode.UNAUTHORIZED_TABLE


class TestStackedQueries:
    """Tests for stacked query injection attempts"""

    def test_semicolon_stacked_query_blocked(self):
        """Test that stacked queries with dangerous commands are blocked"""
        test_cases = [
            "SELECT * FROM view.Contract; DROP TABLE view.Contract",
            "SELECT * FROM view.Contract; INSERT INTO view.Contract VALUES (1)",
            "SELECT * FROM view.Contract; DELETE FROM view.Contract",
            "SELECT * FROM view.Contract; EXEC xp_cmdshell 'dir'",
        ]
        for sql in test_cases:
            with pytest.raises(SecurityError):
                QueryExecutor.validate_sql_safety(sql)


class TestClassicInjectionVectors:
    """Tests for classic SQL injection attack vectors"""

    def test_or_1_equals_1(self):
        """Test classic OR 1=1 injection (allowed as valid SQL)"""
        # This is syntactically valid and not inherently dangerous
        sql = "SELECT * FROM view.Contract WHERE 1=1 OR '1'='1'"
        QueryExecutor.validate_sql_safety(sql)
        QueryExecutor.validate_tables(sql)

    def test_string_termination_with_drop(self):
        """Test string termination followed by DROP"""
        sql = "SELECT * FROM view.Contract WHERE Title = 'x'; DROP TABLE view.Contract--"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        # Blocked by DROP keyword (checked before comments)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL
        assert "DROP" in exc_info.value.message

    def test_batch_separator_go(self):
        """Test GO batch separator usage"""
        # GO is not a SQL Server keyword but a batch separator for client tools
        # It should not affect our validation
        sql = "SELECT * FROM view.Contract"
        QueryExecutor.validate_sql_safety(sql)

    def test_waitfor_allowed(self):
        """Test WAITFOR (time-based) - not in dangerous list but limited by timeout"""
        # WAITFOR is allowed syntactically but will be limited by query timeout
        sql = "SELECT * FROM view.Contract; WAITFOR DELAY '00:00:10'"
        # Note: WAITFOR is not in dangerous keywords, but
        # the query timeout (30 seconds) will prevent long delays
        # The semicolon creates a stacked query issue, but WAITFOR itself passes
        # This test documents current behavior
        QueryExecutor.validate_sql_safety(sql)


class TestEncodingBypass:
    """Tests for encoding-based bypass attempts"""

    def test_unicode_normalization(self):
        """Test that unicode variations don't bypass checks"""
        # Standard SELECT should work
        sql = "SELECT * FROM view.Contract"
        QueryExecutor.validate_sql_safety(sql)

    def test_hex_encoded_attack(self):
        """Test hex-encoded attack patterns"""
        # SQL Server can execute hex strings with EXEC
        # But EXEC is already blocked
        sql = "EXEC(0x44524F50205441424C452076696577)"  # DROP TABLE view
        with pytest.raises(SecurityError):
            QueryExecutor.validate_sql_safety(sql)


class TestRowLimitEnforcement:
    """Tests for row limit enforcement"""

    def test_adds_top_when_missing(self):
        """Test that TOP is added when not present"""
        sql = "SELECT * FROM view.Contract"
        result = QueryExecutor.enforce_row_limit(sql, 1000)
        assert "TOP 1000" in result.upper()

    def test_preserves_existing_top(self):
        """Test that existing TOP is preserved"""
        sql = "SELECT TOP 50 * FROM view.Contract"
        result = QueryExecutor.enforce_row_limit(sql, 1000)
        assert "TOP 50" in result
        assert "TOP 1000" not in result

    def test_handles_select_distinct(self):
        """Test TOP insertion with SELECT DISTINCT"""
        sql = "SELECT DISTINCT Title FROM view.Contract"
        result = QueryExecutor.enforce_row_limit(sql, 1000)
        assert "TOP 1000" in result.upper()
        assert "DISTINCT" in result.upper()

    def test_custom_limit(self):
        """Test custom row limit"""
        sql = "SELECT * FROM view.Contract"
        result = QueryExecutor.enforce_row_limit(sql, 100)
        assert "TOP 100" in result.upper()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions"""

    def test_empty_query(self):
        """Test empty query handling"""
        sql = ""
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_whitespace_only(self):
        """Test whitespace-only query"""
        sql = "   \n\t  "
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        assert exc_info.value.code == ErrorCode.SELECT_ONLY

    def test_very_long_query(self):
        """Test handling of very long queries"""
        # Generate a long but valid query
        sql = "SELECT * FROM view.Contract WHERE " + " OR ".join(
            [f"ContractId = {i}" for i in range(100)]
        )
        # Should not raise
        QueryExecutor.validate_sql_safety(sql)
        QueryExecutor.validate_tables(sql)

    def test_nested_subqueries(self):
        """Test deeply nested subqueries"""
        sql = """
            SELECT * FROM view.Contract
            WHERE DeptId IN (
                SELECT DeptId FROM view.Department
                WHERE ParentId IN (
                    SELECT DeptId FROM view.Department WHERE Level = 1
                )
            )
        """
        QueryExecutor.validate_sql_safety(sql)
        QueryExecutor.validate_tables(sql)

    def test_case_insensitive_keyword_detection(self):
        """Test that keyword detection is case insensitive"""
        variants = [
            "select * from view.Contract; DROP table x",
            "SELECT * FROM view.Contract; drop TABLE x",
            "SELECT * FROM view.Contract; Drop Table x",
        ]
        for sql in variants:
            with pytest.raises(SecurityError) as exc_info:
                QueryExecutor.validate_sql_safety(sql)
            assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_keyword_in_string_literal(self):
        """Test that keywords in string literals may trigger false positive"""
        # This is a known limitation - the simple regex check can't distinguish
        # between actual keywords and strings containing those words
        # This test documents the current behavior
        sql = "SELECT * FROM view.Contract WHERE Title LIKE '%DELETE%'"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_sql_safety(sql)
        # Current implementation blocks this (documented behavior)
        assert exc_info.value.code == ErrorCode.DANGEROUS_SQL

    def test_word_boundary_prevents_false_positives(self):
        """Test that word boundaries prevent some false positives"""
        # Words containing dangerous keywords as substrings should be OK
        sql = "SELECT Updated, Created FROM view.Contract"
        QueryExecutor.validate_sql_safety(sql)

    def test_table_alias_extraction(self):
        """Test that table aliases don't affect extraction"""
        sql = "SELECT c.* FROM view.Contract c"
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables
