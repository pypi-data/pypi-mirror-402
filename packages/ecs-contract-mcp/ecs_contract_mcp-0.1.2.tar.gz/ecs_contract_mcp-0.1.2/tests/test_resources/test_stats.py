"""Tests for Stats Resources (Dynamic)"""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.resources.stats import register_stats_resources


@pytest.fixture
def mcp_server():
    """Create a test MCP server with stats resources"""
    mcp = FastMCP(name="test-server")
    register_stats_resources(mcp)
    return mcp


class TestDashboard:
    """Tests for ecs://stats/dashboard resource"""

    @pytest.mark.asyncio
    async def test_dashboard_returns_formatted_stats(self, mcp_server):
        """Dashboard should return formatted statistics"""
        # Mock data for main stats
        main_stats = [[100, 20, 30, 5, 15, 3]]

        # Mock data for department stats
        dept_stats = [
            ["研發部", 25],
            ["業務部", 20],
            ["法務部", 15],
        ]

        # Mock data for stage stats
        stage_stats = [
            ["法務審核", 10],
            ["主管審核", 8],
            ["結案歸檔", 5],
        ]

        call_count = 0

        async def mock_execute_query(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (["ActiveCount", "MonthlyNew", "PendingApproval", "ExpiringSoon30", "ExpiringSoon90", "BlockedByCoExam"], main_stats)
            elif call_count == 2:
                return (["DepartmentName", "ContractCount"], dept_stats)
            else:
                return (["ExamStageName", "PendingCount"], stage_stats)

        with patch(
            "mcp_server.resources.stats.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=mock_execute_query,
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://stats/dashboard")
            result = await resource.fn()

            # Check main stats
            assert "# ECS 系統概況" in result
            assert "更新時間" in result
            assert "進行中合約" in result
            assert "100" in result
            assert "待審核案件" in result
            assert "30" in result

            # Check department stats
            assert "各部門進行中合約" in result
            assert "研發部" in result
            assert "業務部" in result

            # Check stage stats
            assert "各審核階段待審數量" in result
            assert "法務審核" in result
            assert "主管審核" in result

    @pytest.mark.asyncio
    async def test_dashboard_handles_empty_data(self, mcp_server):
        """Dashboard should handle empty data gracefully"""
        with patch(
            "mcp_server.resources.stats.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=([], []),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://stats/dashboard")
            result = await resource.fn()

            assert "# ECS 系統概況" in result
            assert "無法取得統計資料" in result

    @pytest.mark.asyncio
    async def test_dashboard_handles_error(self, mcp_server):
        """Dashboard should handle database errors gracefully"""
        with patch(
            "mcp_server.resources.stats.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://stats/dashboard")
            result = await resource.fn()

            assert "# ECS 系統概況" in result
            assert "更新時間" in result
            assert "無法取得統計資料" in result

    @pytest.mark.asyncio
    async def test_dashboard_formats_numbers_with_commas(self, mcp_server):
        """Dashboard should format large numbers with commas"""
        main_stats = [[10000, 2500, 3000, 500, 1500, 300]]

        call_count = 0

        async def mock_execute_query(sql, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return (["ActiveCount", "MonthlyNew", "PendingApproval", "ExpiringSoon30", "ExpiringSoon90", "BlockedByCoExam"], main_stats)
            else:
                return ([], [])

        with patch(
            "mcp_server.resources.stats.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=mock_execute_query,
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://stats/dashboard")
            result = await resource.fn()

            # Check number formatting with commas
            assert "10,000" in result
            assert "2,500" in result
            assert "3,000" in result
