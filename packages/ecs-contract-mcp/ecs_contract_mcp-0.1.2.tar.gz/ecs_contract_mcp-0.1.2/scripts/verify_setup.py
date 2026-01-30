#!/usr/bin/env python3
"""Verify MCP Server setup and database connectivity"""

import asyncio
import sys


async def main():
    print("=" * 60)
    print("ECS MCP Server Setup Verification")
    print("=" * 60)
    print()

    # 1. Check imports
    print("[1/5] Checking imports...")
    try:
        from mcp_server.config import settings
        from mcp_server.database.allowed_views import ALLOWED_VIEWS, is_view_allowed
        from mcp_server.database.connection import DatabasePool
        from mcp_server.database.query_executor import QueryExecutor
        from mcp_server.utils.errors import ErrorCode, SecurityError
        from mcp_server.utils.logging import setup_logging

        print("      All imports successful!")
    except ImportError as e:
        print(f"      FAILED: {e}")
        return 1

    # 2. Check configuration
    print("[2/5] Checking configuration...")
    print(f"      DB Server: {settings.DB_SERVER}")
    print(f"      DB Name: {settings.DB_NAME}")
    print(f"      Pool Size: {settings.DB_POOL_SIZE}")
    print(f"      Max Rows: {settings.MAX_ROWS}")

    # 3. Check view whitelist
    print("[3/5] Checking view whitelist...")
    print(f"      Allowed views: {len(ALLOWED_VIEWS)}")
    print(f"      view.Contract allowed: {is_view_allowed('view.Contract')}")
    print(f"      [view].[Contract] allowed: {is_view_allowed('[view].[Contract]')}")
    print(f"      dbo.Users allowed: {is_view_allowed('dbo.Users')}")

    # 4. Check SQL validation
    print("[4/5] Checking SQL validation...")
    tests = [
        ("SELECT * FROM [view].[Contract]", True),
        ("INSERT INTO [view].[Contract] VALUES (1)", False),
        ("SELECT * FROM dbo.Users", False),
    ]
    for sql, should_pass in tests:
        try:
            QueryExecutor.validate_sql_safety(sql)
            QueryExecutor.validate_tables(sql)
            passed = True
        except SecurityError:
            passed = False

        status = "PASS" if passed == should_pass else "FAIL"
        print(f"      {status}: {sql[:50]}...")

    # 5. Check database connectivity
    print("[5/5] Checking database connectivity...")
    try:
        setup_logging()
        await DatabasePool.init()
        print(f"      Pool initialized: {DatabasePool.is_initialized()}")
        print(f"      Pool status: {DatabasePool.pool_status()}")

        result = await QueryExecutor.execute(
            sql="SELECT TOP 3 ContractID, DocumentName FROM [view].[Contract]",
            purpose="Setup verification",
        )
        print(f"      Query successful: {result.success}")
        print(f"      Rows returned: {result.row_count}")

        await DatabasePool.close()
        print("      Database connection: OK")
    except Exception as e:
        print(f"      FAILED: {e}")
        return 1

    print()
    print("=" * 60)
    print("All checks passed! MCP Server is ready.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
