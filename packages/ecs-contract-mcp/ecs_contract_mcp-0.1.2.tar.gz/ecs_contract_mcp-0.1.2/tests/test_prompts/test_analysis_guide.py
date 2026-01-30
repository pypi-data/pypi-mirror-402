"""Tests for analysis guide prompts"""

import pytest

from mcp.server.fastmcp import FastMCP

from mcp_server.prompts.analysis_guide import register_prompts


class TestPromptRegistration:
    """Tests for prompt registration"""

    def test_prompts_registered(self):
        """Test that all prompts are registered"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        # Check prompts are registered
        prompts = mcp._prompt_manager._prompts
        assert "data_analysis_guide" in prompts
        assert "common_queries" in prompts


class TestDataAnalysisGuide:
    """Tests for data_analysis_guide prompt"""

    def test_returns_string(self):
        """Test that prompt returns a string"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("data_analysis_guide")
        assert prompt is not None

        # Call the prompt function
        result = prompt.fn()
        assert isinstance(result, str)

    def test_contains_analysis_steps(self):
        """Test that prompt contains analysis steps"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("data_analysis_guide")
        result = prompt.fn()

        # Check for key sections
        assert "Step 1" in result
        assert "Step 2" in result
        assert "Step 3" in result
        assert "Step 4" in result
        assert "Step 5" in result

    def test_contains_status_conditions(self):
        """Test that prompt contains SQL status conditions"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("data_analysis_guide")
        result = prompt.fn()

        # Check for status conditions
        assert "SaveNo IS NULL" in result
        assert "ContractCategoryId" in result
        assert "ExamStatusId" in result


class TestCommonQueries:
    """Tests for common_queries prompt"""

    def test_returns_string(self):
        """Test that prompt returns a string"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("common_queries")
        assert prompt is not None

        result = prompt.fn()
        assert isinstance(result, str)

    def test_contains_sql_examples(self):
        """Test that prompt contains SQL examples"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("common_queries")
        result = prompt.fn()

        # Check for SQL keywords
        assert "SELECT" in result
        assert "FROM view." in result
        assert "WHERE" in result
        assert "JOIN" in result

    def test_contains_common_scenarios(self):
        """Test that prompt contains common scenario examples"""
        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("common_queries")
        result = prompt.fn()

        # Check for common scenarios
        assert "到期" in result
        assert "部門" in result
        assert "審核" in result
        assert "會辦" in result

    def test_all_views_are_allowed(self):
        """Test that all views in examples are in allowed list"""
        from mcp_server.database.allowed_views import is_view_allowed

        mcp = FastMCP(name="test")
        register_prompts(mcp)

        prompts = mcp._prompt_manager._prompts
        prompt = prompts.get("common_queries")
        result = prompt.fn()

        # Extract view names from the prompt
        import re

        # Pattern to find view.XXX references
        pattern = r"view\.(\w+)"
        matches = re.findall(pattern, result)

        # Check each view is allowed
        for view_name in matches:
            full_name = f"view.{view_name}"
            assert is_view_allowed(full_name), f"View {full_name} is not in allowed list"
