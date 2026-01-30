#!/usr/bin/env python3
"""End-to-end test script for ECS MCP Server

This script tests the MCP Server's core functionality including:
1. Server startup
2. Resource listing and reading
3. Tool execution
4. Security mechanisms
5. Error handling

Usage:
    python scripts/e2e_test.py

Prerequisites:
    - Set environment variables: DB_SERVER, DB_NAME, DB_USER, DB_PASSWORD
    - Or create a .env file in the project root
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class E2ETestRunner:
    """End-to-end test runner for ECS MCP Server"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log a message with level indicator"""
        prefix = {
            "INFO": "ℹ️ ",
            "PASS": "✅",
            "FAIL": "❌",
            "WARN": "⚠️ ",
            "TEST": "🧪",
        }.get(level, "  ")
        print(f"{prefix} {message}")

    def record_result(self, test_name: str, passed: bool, error: str | None = None):
        """Record a test result"""
        if passed:
            self.passed += 1
            self.log(f"{test_name}", "PASS")
        else:
            self.failed += 1
            error_msg = f"{test_name}: {error}" if error else test_name
            self.errors.append(error_msg)
            self.log(f"{test_name}: {error}", "FAIL")

    async def test_config_loading(self) -> bool:
        """Test configuration loading"""
        self.log("Testing configuration loading...", "TEST")
        try:
            from mcp_server.config import settings

            # Check required settings exist
            assert settings.DB_SERVER, "DB_SERVER not configured"
            assert settings.DB_NAME, "DB_NAME not configured"
            assert settings.DB_USER, "DB_USER not configured"
            assert settings.DB_PASSWORD, "DB_PASSWORD not configured"

            self.record_result("Config loading", True)
            return True
        except Exception as e:
            self.record_result("Config loading", False, str(e))
            return False

    async def test_allowed_views(self) -> bool:
        """Test allowed views whitelist"""
        self.log("Testing allowed views whitelist...", "TEST")
        try:
            from mcp_server.database.allowed_views import (
                ALLOWED_VIEWS,
                get_allowed_views,
                is_view_allowed,
            )

            # Test whitelist not empty
            assert len(ALLOWED_VIEWS) >= 35, f"Expected >=35 views, got {len(ALLOWED_VIEWS)}"

            # Test core views present
            core_views = ["view.Contract", "view.Partner", "view.Department"]
            for view in core_views:
                assert is_view_allowed(view), f"Core view {view} not allowed"

            # Test disallowed views
            disallowed = ["dbo.Users", "sys.tables", "master.dbo.sysdatabases"]
            for view in disallowed:
                assert not is_view_allowed(view), f"{view} should NOT be allowed"

            # Test bracket format
            assert is_view_allowed("[view].[Contract]"), "Bracket format should work"

            self.record_result("Allowed views whitelist", True)
            return True
        except Exception as e:
            self.record_result("Allowed views whitelist", False, str(e))
            return False

    async def test_sql_validation(self) -> bool:
        """Test SQL validation security"""
        self.log("Testing SQL validation...", "TEST")
        try:
            from mcp_server.database.query_executor import QueryExecutor
            from mcp_server.utils.errors import SecurityError

            # Test valid SELECT passes
            QueryExecutor.validate_sql_safety("SELECT * FROM view.Contract")
            QueryExecutor.validate_sql_safety("SELECT TOP 100 * FROM view.Contract")

            # Test dangerous statements blocked
            dangerous_sqls = [
                ("INSERT INTO view.Contract VALUES (1)", "INSERT"),
                ("DELETE FROM view.Contract", "DELETE"),
                ("UPDATE view.Contract SET Title = 'x'", "UPDATE"),
                ("DROP TABLE view.Contract", "DROP"),
                ("SELECT * FROM view.Contract; EXEC sp_help", "EXEC"),
                ("SELECT * FROM view.Contract -- comment", "Comment"),
            ]

            for sql, attack_type in dangerous_sqls:
                try:
                    QueryExecutor.validate_sql_safety(sql)
                    self.record_result(f"SQL validation - {attack_type}", False, "Should have been blocked")
                    return False
                except SecurityError:
                    pass  # Expected

            self.record_result("SQL validation", True)
            return True
        except Exception as e:
            self.record_result("SQL validation", False, str(e))
            return False

    async def test_table_validation(self) -> bool:
        """Test table/view whitelist validation"""
        self.log("Testing table validation...", "TEST")
        try:
            from mcp_server.database.query_executor import QueryExecutor
            from mcp_server.utils.errors import SecurityError

            # Test allowed tables pass
            QueryExecutor.validate_tables("SELECT * FROM view.Contract")
            QueryExecutor.validate_tables("SELECT * FROM [view].[Contract]")

            # Test disallowed tables blocked
            disallowed_sqls = [
                "SELECT * FROM dbo.Users",
                "SELECT * FROM sys.tables",
                "SELECT * FROM view.Contract JOIN dbo.SensitiveData ON 1=1",
            ]

            for sql in disallowed_sqls:
                try:
                    QueryExecutor.validate_tables(sql)
                    self.record_result("Table validation", False, f"Should have blocked: {sql[:50]}")
                    return False
                except SecurityError:
                    pass  # Expected

            self.record_result("Table validation", True)
            return True
        except Exception as e:
            self.record_result("Table validation", False, str(e))
            return False

    async def test_row_limit_enforcement(self) -> bool:
        """Test row limit enforcement"""
        self.log("Testing row limit enforcement...", "TEST")
        try:
            from mcp_server.database.query_executor import QueryExecutor

            # Test TOP added when missing
            sql = "SELECT * FROM view.Contract"
            result = QueryExecutor.enforce_row_limit(sql, 1000)
            assert "TOP 1000" in result.upper(), "TOP should be added"

            # Test existing TOP preserved
            sql = "SELECT TOP 50 * FROM view.Contract"
            result = QueryExecutor.enforce_row_limit(sql, 1000)
            assert "TOP 50" in result, "Existing TOP should be preserved"
            assert "TOP 1000" not in result, "Should not add another TOP"

            # Test DISTINCT handled
            sql = "SELECT DISTINCT Title FROM view.Contract"
            result = QueryExecutor.enforce_row_limit(sql, 100)
            assert "TOP 100" in result.upper(), "TOP should be added with DISTINCT"
            assert "DISTINCT" in result.upper(), "DISTINCT should be preserved"

            self.record_result("Row limit enforcement", True)
            return True
        except Exception as e:
            self.record_result("Row limit enforcement", False, str(e))
            return False

    async def test_database_connection(self) -> bool:
        """Test database connection"""
        self.log("Testing database connection...", "TEST")
        try:
            from mcp_server.database.connection import DatabasePool

            # Initialize pool
            await DatabasePool.init()

            # Test simple query
            columns, rows = await DatabasePool.execute_query(
                "SELECT TOP 1 ContractId FROM [view].[Contract]"
            )

            assert columns is not None, "Columns should not be None"
            assert len(columns) > 0, "Should have at least one column"

            # Close pool
            await DatabasePool.close()

            self.record_result("Database connection", True)
            return True
        except Exception as e:
            self.record_result("Database connection", False, str(e))
            return False

    async def test_query_executor_integration(self) -> bool:
        """Test query executor end-to-end"""
        self.log("Testing query executor integration...", "TEST")
        try:
            from mcp_server.database.connection import DatabasePool
            from mcp_server.database.query_executor import QueryExecutor

            # Initialize connection
            await DatabasePool.init()

            # Test successful query
            result = await QueryExecutor.execute(
                sql="SELECT TOP 5 ContractId, Title FROM view.Contract",
                purpose="E2E test - query contracts",
            )

            assert result.success, "Query should succeed"
            assert len(result.columns) >= 2, "Should have at least 2 columns"
            assert result.row_count <= 5, "Should respect TOP limit"

            # Test security blocking
            from mcp_server.utils.errors import SecurityError

            try:
                await QueryExecutor.execute(
                    sql="SELECT * FROM dbo.Users",
                    purpose="E2E test - should be blocked",
                )
                self.record_result("Query executor integration", False, "Should have blocked unauthorized table")
                return False
            except SecurityError:
                pass  # Expected

            await DatabasePool.close()

            self.record_result("Query executor integration", True)
            return True
        except Exception as e:
            self.record_result("Query executor integration", False, str(e))
            return False

    async def test_mcp_server_initialization(self) -> bool:
        """Test MCP server can be initialized"""
        self.log("Testing MCP server initialization...", "TEST")
        try:
            from mcp_server.server import mcp

            # Check server is configured
            assert mcp.name == "ecs-contract-mcp", f"Server name mismatch: {mcp.name}"

            # Check tools registered
            tools = mcp._tool_manager._tools
            assert "query_database" in tools, "query_database tool not registered"

            self.record_result("MCP server initialization", True)
            return True
        except Exception as e:
            self.record_result("MCP server initialization", False, str(e))
            return False

    async def test_resources_available(self) -> bool:
        """Test MCP resources are available"""
        self.log("Testing MCP resources...", "TEST")
        try:
            from mcp_server.server import mcp

            # Get registered resources
            resources = mcp._resource_manager._resources

            expected_resources = [
                "ecs://schema/overview",
                "ecs://schema/views",
                "ecs://context/business-terms",
            ]

            for uri in expected_resources:
                assert uri in resources, f"Resource {uri} not registered"

            self.record_result("MCP resources available", True)
            return True
        except Exception as e:
            self.record_result("MCP resources available", False, str(e))
            return False

    async def test_prompts_available(self) -> bool:
        """Test MCP prompts are available"""
        self.log("Testing MCP prompts...", "TEST")
        try:
            from mcp_server.server import mcp

            # Get registered prompts
            prompts = mcp._prompt_manager._prompts

            expected_prompts = ["data_analysis_guide", "common_queries"]

            for name in expected_prompts:
                assert name in prompts, f"Prompt {name} not registered"

            self.record_result("MCP prompts available", True)
            return True
        except Exception as e:
            self.record_result("MCP prompts available", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all tests"""
        print("\n" + "=" * 60)
        print("ECS MCP Server - End-to-End Tests")
        print("=" * 60 + "\n")

        # Run tests in order
        tests = [
            self.test_config_loading,
            self.test_allowed_views,
            self.test_sql_validation,
            self.test_table_validation,
            self.test_row_limit_enforcement,
            self.test_mcp_server_initialization,
            self.test_resources_available,
            self.test_prompts_available,
            self.test_database_connection,
            self.test_query_executor_integration,
        ]

        for test in tests:
            try:
                await test()
            except Exception as e:
                self.record_result(test.__name__, False, f"Unexpected error: {e}")

        # Print summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📊 Total:  {self.passed + self.failed}")

        if self.errors:
            print("\nFailed Tests:")
            for error in self.errors:
                print(f"  • {error}")

        return self.failed == 0


async def main():
    """Main entry point"""
    # Load environment variables from .env if available
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        from dotenv import load_dotenv

        load_dotenv(env_file)

    # Check required environment variables
    required_vars = ["DB_SERVER", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("   Some tests will be skipped.")

    runner = E2ETestRunner()
    success = await runner.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
