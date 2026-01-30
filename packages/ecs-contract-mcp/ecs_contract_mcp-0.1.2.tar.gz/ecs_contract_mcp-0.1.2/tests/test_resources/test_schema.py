"""Tests for Schema Resources"""

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_server.resources.schema import register_schema_resources


@pytest.fixture
def mcp_server():
    """Create a test MCP server with schema resources"""
    mcp = FastMCP(name="test-server")
    register_schema_resources(mcp)
    return mcp


class TestSchemaOverview:
    """Tests for ecs://schema/overview resource"""

    def test_overview_returns_string(self, mcp_server):
        """Overview resource should return a string"""
        # Get the resource handler
        resource = mcp_server._resource_manager._resources.get("ecs://schema/overview")
        assert resource is not None

        # Call the handler
        result = resource.fn()
        assert isinstance(result, str)

    def test_overview_contains_basic_info(self, mcp_server):
        """Overview should contain database basic info"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/overview")
        result = resource.fn()

        assert "LT_ECS_LTCCore" in result
        assert "SQL Server" in result
        assert "187" in result  # table count
        assert "70" in result   # view count

    def test_overview_contains_schema_distribution(self, mcp_server):
        """Overview should contain schema distribution"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/overview")
        result = resource.fn()

        assert "code" in result
        assert "data" in result
        assert "join" in result
        assert "dbo" in result


class TestSchemaViews:
    """Tests for ecs://schema/views resource"""

    def test_views_returns_string(self, mcp_server):
        """Views resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/views")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_views_contains_view_list(self, mcp_server):
        """Views should contain the view whitelist"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/views")
        result = resource.fn()

        # Check core views are listed
        assert "view.Contract" in result
        assert "view.ContractHistory" in result
        assert "view.Partner" in result
        assert "view.Department" in result
        assert "view.OtherExaminer" in result

    def test_views_contains_field_info(self, mcp_server):
        """Views should contain field information"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/views")
        result = resource.fn()

        # Check important fields are documented
        assert "ContractId" in result
        assert "SaveNo" in result
        assert "PartnerId" in result
        assert "DepartmentId" in result

    def test_views_contains_status_definitions(self, mcp_server):
        """Views should contain status definitions"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/views")
        result = resource.fn()

        # Check status definitions
        assert "ContractCategoryId = 1" in result  # Sales
        assert "ContractCategoryId = 2" in result  # Purchase
        assert "ExamStatusId = 1" in result  # Approved
        assert "ExamStatusId = 2" in result  # Returned


class TestSchemaRelationships:
    """Tests for ecs://schema/relationships resource"""

    def test_relationships_returns_string(self, mcp_server):
        """Relationships resource should return a string"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/relationships")
        assert resource is not None

        result = resource.fn()
        assert isinstance(result, str)

    def test_relationships_contains_diagram(self, mcp_server):
        """Relationships should contain entity diagram"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/relationships")
        result = resource.fn()

        # Check diagram elements
        assert "Contract" in result
        assert "Partner" in result
        assert "Department" in result
        assert "ContractHistory" in result

    def test_relationships_contains_foreign_keys(self, mcp_server):
        """Relationships should contain foreign key info"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/relationships")
        result = resource.fn()

        # Check foreign key relationships
        assert "PartnerId" in result
        assert "DepartmentId" in result
        assert "ContractTypeId" in result

    def test_relationships_contains_join_examples(self, mcp_server):
        """Relationships should contain JOIN examples"""
        resource = mcp_server._resource_manager._resources.get("ecs://schema/relationships")
        result = resource.fn()

        # Check SQL examples
        assert "JOIN" in result
        assert "SELECT" in result
