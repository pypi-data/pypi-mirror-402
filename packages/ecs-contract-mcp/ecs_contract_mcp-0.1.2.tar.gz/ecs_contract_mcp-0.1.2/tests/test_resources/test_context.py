"""Tests for Context Resources"""

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.resources.context import register_context_resources


@pytest.fixture
def mcp_server():
    """Create a test MCP server with context resources"""
    mcp = FastMCP(name="test-server")
    register_context_resources(mcp)
    return mcp


class TestBusinessTerms:
    """Tests for ecs://context/business-terms resource"""

    def test_business_terms_returns_string(self, mcp_server):
        """Business terms resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/business-terms")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_business_terms_contains_contract_categories(self, mcp_server):
        """Business terms should contain contract categories"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/business-terms")
        result = resource.fn()

        assert "ContractCategoryId = 1" in result
        assert "ContractCategoryId = 2" in result
        assert "ContractCategoryId = 3" in result

    def test_business_terms_contains_status_definitions(self, mcp_server):
        """Business terms should contain status definitions"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/business-terms")
        result = resource.fn()

        assert "SaveNo IS NULL" in result
        assert "SaveNo IS NOT NULL" in result

    def test_business_terms_contains_co_exam_status(self, mcp_server):
        """Business terms should contain co-examination status"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/business-terms")
        result = resource.fn()

        assert "Halt = 1 AND Replied = 0" in result


class TestContractLifecycle:
    """Tests for ecs://context/contract-lifecycle resource"""

    def test_contract_lifecycle_returns_string(self, mcp_server):
        """Contract lifecycle resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/contract-lifecycle")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_contract_lifecycle_contains_stages(self, mcp_server):
        """Contract lifecycle should contain exam stages"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/contract-lifecycle")
        result = resource.fn()

        assert "ExamStageId = 1" in result  # Applicant
        assert "ExamStageId = 2" in result  # Director
        assert "ExamStageId = 5" in result  # Legal Review

    def test_contract_lifecycle_contains_flow_diagram(self, mcp_server):
        """Contract lifecycle should contain flow diagram"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/contract-lifecycle")
        result = resource.fn()

        assert "申請人" in result
        assert "主管審核" in result
        assert "法務審核" in result
        assert "結案歸檔" in result


class TestApprovalFlow:
    """Tests for ecs://context/approval-flow resource"""

    def test_approval_flow_returns_string(self, mcp_server):
        """Approval flow resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/approval-flow")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_approval_flow_contains_stage_list(self, mcp_server):
        """Approval flow should contain exam stage list"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/approval-flow")
        result = resource.fn()

        assert "Applicant" in result
        assert "DirectorApproval" in result
        assert "LegalReview" in result

    def test_approval_flow_contains_status_definitions(self, mcp_server):
        """Approval flow should contain exam status definitions"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/approval-flow")
        result = resource.fn()

        assert "ExamStatusId" in result
        assert "通過" in result
        assert "退回" in result
        assert "審核中" in result

    def test_approval_flow_contains_co_exam_mechanism(self, mcp_server):
        """Approval flow should contain co-examination mechanism"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/approval-flow")
        result = resource.fn()

        assert "Halt" in result
        assert "Replied" in result
        assert "會辦" in result


class TestSlaDefinitions:
    """Tests for ecs://context/sla-definitions resource"""

    def test_sla_definitions_returns_string(self, mcp_server):
        """SLA definitions resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/sla-definitions")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_sla_definitions_contains_standard_days(self, mcp_server):
        """SLA definitions should contain standard processing days"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/sla-definitions")
        result = resource.fn()

        assert "標準天數" in result
        assert "3 天" in result
        assert "5 天" in result

    def test_sla_definitions_contains_urgent_levels(self, mcp_server):
        """SLA definitions should contain urgent levels"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/sla-definitions")
        result = resource.fn()

        assert "UrgentLevel" in result
        assert "一般" in result
        assert "急件" in result
        assert "特急" in result

    def test_sla_definitions_contains_overdue_queries(self, mcp_server):
        """SLA definitions should contain overdue query examples"""
        resource = mcp_server._resource_manager._resources.get("ecs://context/sla-definitions")
        result = resource.fn()

        assert "DATEDIFF" in result
        assert "StayDate" in result
