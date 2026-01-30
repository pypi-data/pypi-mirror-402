"""Tests for View whitelist mechanism

This module contains comprehensive tests for the view whitelist security mechanism.
"""

import pytest

from mcp_server.database.allowed_views import (
    ALLOWED_VIEWS,
    ALLOWED_VIEWS_SET,
    get_allowed_views,
    get_allowed_views_bracketed,
    is_view_allowed,
    normalize_table_name,
)
from mcp_server.database.query_executor import QueryExecutor
from mcp_server.utils.errors import ErrorCode, SecurityError


class TestNormalizeTableName:
    """Tests for table name normalization"""

    def test_simple_format(self):
        """Test normalization of simple schema.table format"""
        assert normalize_table_name("view.Contract") == "view.Contract"
        assert normalize_table_name("dbo.Users") == "dbo.Users"

    def test_bracket_format(self):
        """Test normalization of [schema].[table] format"""
        assert normalize_table_name("[view].[Contract]") == "view.Contract"
        assert normalize_table_name("[dbo].[Users]") == "dbo.Users"

    def test_mixed_format(self):
        """Test normalization of mixed formats"""
        assert normalize_table_name("[view].Contract") == "view.Contract"
        assert normalize_table_name("view.[Contract]") == "view.Contract"

    def test_preserves_case(self):
        """Test that case is preserved"""
        assert normalize_table_name("View.CONTRACT") == "View.CONTRACT"
        assert normalize_table_name("[VIEW].[contract]") == "VIEW.contract"


class TestIsViewAllowed:
    """Tests for view whitelist checking"""

    def test_allowed_views(self):
        """Test that all defined allowed views pass"""
        for view in ALLOWED_VIEWS:
            assert is_view_allowed(view), f"{view} should be allowed"

    def test_allowed_views_bracket_format(self):
        """Test allowed views with bracket format"""
        assert is_view_allowed("[view].[Contract]")
        assert is_view_allowed("[view].[Partner]")
        assert is_view_allowed("[view].[Department]")

    def test_disallowed_views(self):
        """Test that non-whitelisted views are rejected"""
        disallowed = [
            "dbo.Contract",
            "dbo.Users",
            "sys.tables",
            "master.dbo.sysdatabases",
            "view.NonExistentView",
            "public.Contract",
        ]
        for view in disallowed:
            assert not is_view_allowed(view), f"{view} should NOT be allowed"

    def test_case_sensitivity(self):
        """Test case sensitivity in view matching"""
        # The whitelist stores views as "view.Contract", so different cases won't match
        assert is_view_allowed("view.Contract")
        assert not is_view_allowed("VIEW.CONTRACT")
        assert not is_view_allowed("view.contract")


class TestGetAllowedViews:
    """Tests for allowed views list retrieval"""

    def test_get_allowed_views_returns_list(self):
        """Test that get_allowed_views returns a list"""
        views = get_allowed_views()
        assert isinstance(views, list)
        assert len(views) > 0

    def test_get_allowed_views_returns_copy(self):
        """Test that get_allowed_views returns a copy"""
        views1 = get_allowed_views()
        views2 = get_allowed_views()
        views1.append("test.View")
        assert "test.View" not in views2

    def test_get_allowed_views_bracketed(self):
        """Test bracket format retrieval"""
        bracketed = get_allowed_views_bracketed()
        assert isinstance(bracketed, list)
        for view in bracketed:
            assert view.startswith("[")
            assert "].[" in view
            assert view.endswith("]")

    def test_allowed_views_set_contains_all(self):
        """Test that the set contains all views"""
        for view in ALLOWED_VIEWS:
            assert view in ALLOWED_VIEWS_SET


class TestExtractTablesFromSql:
    """Tests for SQL table extraction"""

    def test_simple_from(self):
        """Test extraction from simple FROM clause"""
        sql = "SELECT * FROM view.Contract"
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables

    def test_bracket_from(self):
        """Test extraction from bracketed FROM clause"""
        sql = "SELECT * FROM [view].[Contract]"
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables

    def test_multiple_joins(self):
        """Test extraction with multiple JOINs"""
        sql = """
            SELECT c.*, p.Name, d.DeptName
            FROM view.Contract c
            JOIN view.Partner p ON c.PartnerId = p.PartnerId
            LEFT JOIN view.Department d ON c.DeptId = d.DeptId
        """
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables
        assert "view.Partner" in tables
        assert "view.Department" in tables

    def test_mixed_formats(self):
        """Test extraction with mixed bracket/non-bracket formats"""
        sql = """
            SELECT *
            FROM [view].[Contract] c
            JOIN view.Partner p ON c.PartnerId = p.PartnerId
        """
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables
        assert "view.Partner" in tables

    def test_subquery(self):
        """Test extraction with subquery"""
        sql = """
            SELECT *
            FROM view.Contract c
            WHERE c.DeptId IN (
                SELECT DeptId FROM view.Department WHERE Active = 1
            )
        """
        tables = QueryExecutor.extract_tables_from_sql(sql)
        assert "view.Contract" in tables
        assert "view.Department" in tables


class TestValidateTables:
    """Tests for table validation in queries"""

    def test_valid_single_table(self):
        """Test validation of single allowed table"""
        sql = "SELECT * FROM view.Contract"
        # Should not raise
        QueryExecutor.validate_tables(sql)

    def test_valid_multiple_tables(self):
        """Test validation of multiple allowed tables"""
        sql = """
            SELECT c.*, p.Name
            FROM view.Contract c
            JOIN view.Partner p ON c.PartnerId = p.PartnerId
        """
        QueryExecutor.validate_tables(sql)

    def test_invalid_table_raises(self):
        """Test that invalid table raises SecurityError"""
        sql = "SELECT * FROM dbo.SomeTable"
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_tables(sql)
        assert exc_info.value.code == ErrorCode.UNAUTHORIZED_TABLE

    def test_mixed_valid_invalid_raises(self):
        """Test that query with one invalid table raises"""
        sql = """
            SELECT c.*, s.*
            FROM view.Contract c
            JOIN dbo.SensitiveData s ON c.Id = s.ContractId
        """
        with pytest.raises(SecurityError) as exc_info:
            QueryExecutor.validate_tables(sql)
        assert exc_info.value.code == ErrorCode.UNAUTHORIZED_TABLE
        assert "dbo.SensitiveData" in exc_info.value.message

    def test_system_tables_blocked(self):
        """Test that system tables are blocked"""
        system_tables = [
            "sys.tables",
            "sys.columns",
            "sys.objects",
            "INFORMATION_SCHEMA.TABLES",
            "INFORMATION_SCHEMA.COLUMNS",
        ]
        for table in system_tables:
            sql = f"SELECT * FROM {table}"
            with pytest.raises(SecurityError):
                QueryExecutor.validate_tables(sql)


class TestWhitelistCompleteness:
    """Tests to verify whitelist completeness"""

    def test_minimum_views_count(self):
        """Test that minimum number of views are defined"""
        # Based on dev-mcp-views.md, we should have 37 views
        assert len(ALLOWED_VIEWS) >= 35

    def test_core_views_present(self):
        """Test that core business views are present"""
        core_views = [
            "view.Contract",
            "view.Partner",
            "view.Department",
            "view.User",
            "view.Role",
        ]
        for view in core_views:
            assert view in ALLOWED_VIEWS_SET, f"Core view {view} missing"

    def test_all_views_in_view_schema(self):
        """Test that all allowed views are in the 'view' schema"""
        for view in ALLOWED_VIEWS:
            assert view.startswith("view."), f"{view} should be in 'view' schema"

    def test_no_sensitive_schemas(self):
        """Test that no sensitive schemas are allowed"""
        sensitive_prefixes = ["dbo.", "sys.", "master.", "tempdb.", "msdb."]
        for view in ALLOWED_VIEWS:
            for prefix in sensitive_prefixes:
                assert not view.lower().startswith(
                    prefix.lower()
                ), f"{view} uses sensitive schema {prefix}"
