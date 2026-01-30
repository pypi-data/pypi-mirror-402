"""Tests for query_database tool"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from mcp_server.database.query_executor import QueryResult
from mcp_server.tools.query import serialize_row, serialize_value


class TestSerializeValue:
    """Tests for serialize_value function"""

    def test_none(self):
        """Test None serialization"""
        assert serialize_value(None) is None

    def test_datetime(self):
        """Test datetime serialization"""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        result = serialize_value(dt)
        assert result == "2024-01-15T10:30:00"

    def test_date(self):
        """Test date serialization"""
        d = date(2024, 1, 15)
        result = serialize_value(d)
        assert result == "2024-01-15"

    def test_decimal(self):
        """Test decimal serialization"""
        d = Decimal("12345.67")
        result = serialize_value(d)
        assert result == "12345.67"
        assert isinstance(result, str)

    def test_bytes(self):
        """Test bytes serialization"""
        b = b"\x00\x01\x02\xff"
        result = serialize_value(b)
        assert result == "000102ff"

    def test_string(self):
        """Test string passthrough"""
        s = "Hello World"
        result = serialize_value(s)
        assert result == s

    def test_int(self):
        """Test int passthrough"""
        i = 12345
        result = serialize_value(i)
        assert result == i

    def test_bool(self):
        """Test bool passthrough"""
        assert serialize_value(True) is True
        assert serialize_value(False) is False


class TestSerializeRow:
    """Tests for serialize_row function"""

    def test_mixed_types(self):
        """Test serialization of mixed types in a row"""
        row = [
            1,
            "Test",
            datetime(2024, 1, 15, 10, 30),
            Decimal("100.50"),
            None,
            True,
        ]
        result = serialize_row(row)
        assert result == [
            1,
            "Test",
            "2024-01-15T10:30:00",
            "100.50",
            None,
            True,
        ]


class TestQueryDatabaseTool:
    """Tests for query_database tool (unit tests without actual DB)"""

    @pytest.fixture
    def mock_query_result(self):
        """Create a mock QueryResult"""
        return QueryResult(
            success=True,
            columns=["ContractId", "Title", "CreateDate", "Cost"],
            rows=[
                [1, "Contract A", datetime(2024, 1, 15), Decimal("1000.00")],
                [2, "Contract B", datetime(2024, 2, 20), Decimal("2000.50")],
            ],
            row_count=2,
            truncated=False,
            execution_time_ms=50,
            message=None,
        )

    @pytest.fixture
    def mock_truncated_result(self):
        """Create a mock truncated QueryResult"""
        return QueryResult(
            success=True,
            columns=["ContractId", "Title"],
            rows=[[i, f"Contract {i}"] for i in range(1000)],
            row_count=1000,
            truncated=True,
            execution_time_ms=100,
            message=None,
        )

    @pytest.mark.asyncio
    async def test_successful_query(self, mock_query_result):
        """Test successful query execution"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        # Get the registered tool
        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")
        assert query_tool is not None

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            return_value=mock_query_result,
        ):
            # Call the tool function directly
            result = await query_tool.fn(
                sql="SELECT ContractId, Title FROM view.Contract",
                purpose="Test query",
            )

            assert result["success"] is True
            assert result["columns"] == ["ContractId", "Title", "CreateDate", "Cost"]
            assert result["row_count"] == 2
            assert result["truncated"] is False
            assert result["message"] is None

            # Check serialization
            assert result["rows"][0][2] == "2024-01-15T00:00:00"
            assert result["rows"][0][3] == "1000.00"

    @pytest.mark.asyncio
    async def test_truncated_result(self, mock_truncated_result):
        """Test handling of truncated results"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            return_value=mock_truncated_result,
        ):
            result = await query_tool.fn(
                sql="SELECT ContractId, Title FROM view.Contract",
                purpose="Test query",
            )

            assert result["success"] is True
            assert result["truncated"] is True
            assert result["row_count"] == 1000
            assert "截斷" in result["message"]

    @pytest.mark.asyncio
    async def test_security_error(self):
        """Test handling of security errors"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools
        from mcp_server.utils.errors import ErrorCode, SecurityError

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            side_effect=SecurityError(
                ErrorCode.UNAUTHORIZED_TABLE,
                "Table 'dbo.SomeTable' is not allowed",
            ),
        ):
            result = await query_tool.fn(
                sql="SELECT * FROM dbo.SomeTable",
                purpose="Test query",
            )

            assert result["success"] is False
            assert result["row_count"] == 0
            assert "安全錯誤" in result["message"]

    @pytest.mark.asyncio
    async def test_query_error(self):
        """Test handling of query execution errors"""
        from mcp.server.fastmcp import FastMCP

        from mcp_server.tools.query import register_tools

        mcp = FastMCP(name="test")
        register_tools(mcp)

        tools = mcp._tool_manager._tools
        query_tool = tools.get("query_database")

        with patch(
            "mcp_server.tools.query.QueryExecutor.execute",
            new_callable=AsyncMock,
            side_effect=Exception("Invalid column name 'Foo'"),
        ):
            result = await query_tool.fn(
                sql="SELECT Foo FROM view.Contract",
                purpose="Test query",
            )

            assert result["success"] is False
            assert result["row_count"] == 0
            assert "查詢錯誤" in result["message"]
            assert "Invalid column name" in result["message"]
