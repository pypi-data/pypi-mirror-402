"""Tests for Reference Resources (Dynamic)"""

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.resources.reference import register_reference_resources


@pytest.fixture
def mcp_server():
    """Create a test MCP server with reference resources"""
    mcp = FastMCP(name="test-server")
    register_reference_resources(mcp)
    return mcp


class TestContractTypes:
    """Tests for ecs://reference/contract-types resource"""

    @pytest.mark.asyncio
    async def test_contract_types_returns_formatted_table(self, mcp_server):
        """Contract types should return formatted markdown table"""
        mock_rows = [
            [1, "一般銷售合約", 1],
            [2, "框架合約", 1],
            [3, "採購合約", 2],
        ]

        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=(["ContractTypeId", "ContractTypeName", "ContractCategoryId"], mock_rows),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/contract-types")
            result = await resource.fn()

            assert "# 合約類型清單" in result
            assert "一般銷售合約" in result
            assert "採購合約" in result
            assert "銷售" in result
            assert "採購" in result
            assert "共 3 個合約類型" in result

    @pytest.mark.asyncio
    async def test_contract_types_handles_error(self, mcp_server):
        """Contract types should handle database errors gracefully"""
        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/contract-types")
            result = await resource.fn()

            assert "# 合約類型清單" in result
            assert "無法取得資料" in result


class TestDepartments:
    """Tests for ecs://reference/departments resource"""

    @pytest.mark.asyncio
    async def test_departments_returns_formatted_table(self, mcp_server):
        """Departments should return formatted markdown table"""
        mock_rows = [
            [1, "總經理室", "CEO", 1],
            [2, "研發部", "RD", 2],
            [3, "業務部", "SALES", 2],
        ]

        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=(["DepartmentId", "DepartmentName", "DepartmentCode", "Level"], mock_rows),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/departments")
            result = await resource.fn()

            assert "# 部門清單" in result
            assert "總經理室" in result
            assert "研發部" in result
            assert "CEO" in result
            assert "共 3 個部門" in result

    @pytest.mark.asyncio
    async def test_departments_handles_error(self, mcp_server):
        """Departments should handle database errors gracefully"""
        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/departments")
            result = await resource.fn()

            assert "# 部門清單" in result
            assert "無法取得資料" in result


class TestExamStages:
    """Tests for ecs://reference/exam-stages resource"""

    @pytest.mark.asyncio
    async def test_exam_stages_returns_formatted_table(self, mcp_server):
        """Exam stages should return formatted markdown table"""
        mock_rows = [
            [1, "申請人", "Applicant"],
            [2, "主管審核", "DirectorApproval"],
            [5, "法務審核", "LegalReview"],
        ]

        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=(["ExamStageId", "ExamStageName", "ExamStageCode"], mock_rows),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/exam-stages")
            result = await resource.fn()

            assert "# 審核階段清單" in result
            assert "申請人" in result
            assert "主管審核" in result
            assert "Applicant" in result
            assert "共 3 個審核階段" in result

    @pytest.mark.asyncio
    async def test_exam_stages_contains_explanations(self, mcp_server):
        """Exam stages should contain stage explanations"""
        mock_rows = [[1, "申請人", "Applicant"]]

        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=(["ExamStageId", "ExamStageName", "ExamStageCode"], mock_rows),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/exam-stages")
            result = await resource.fn()

            assert "常用階段說明" in result

    @pytest.mark.asyncio
    async def test_exam_stages_handles_error(self, mcp_server):
        """Exam stages should handle database errors gracefully"""
        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/exam-stages")
            result = await resource.fn()

            assert "# 審核階段清單" in result
            assert "無法取得資料" in result


class TestCurrencies:
    """Tests for ecs://reference/currencies resource"""

    @pytest.mark.asyncio
    async def test_currencies_returns_formatted_table(self, mcp_server):
        """Currencies should return formatted markdown table"""
        mock_rows = [
            [1, "新台幣", "TWD"],
            [2, "美元", "USD"],
            [3, "人民幣", "CNY"],
        ]

        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            return_value=(["ExchangeTypeId", "ExchangeName", "ExchangeCode"], mock_rows),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/currencies")
            result = await resource.fn()

            assert "# 幣別清單" in result
            assert "新台幣" in result
            assert "TWD" in result
            assert "USD" in result
            assert "共 3 種幣別" in result

    @pytest.mark.asyncio
    async def test_currencies_handles_error(self, mcp_server):
        """Currencies should handle database errors gracefully"""
        with patch(
            "mcp_server.resources.reference.DatabasePool.execute_query",
            new_callable=AsyncMock,
            side_effect=Exception("Database connection failed"),
        ):
            resource = mcp_server._resource_manager._resources.get("ecs://reference/currencies")
            result = await resource.fn()

            assert "# 幣別清單" in result
            assert "無法取得資料" in result
