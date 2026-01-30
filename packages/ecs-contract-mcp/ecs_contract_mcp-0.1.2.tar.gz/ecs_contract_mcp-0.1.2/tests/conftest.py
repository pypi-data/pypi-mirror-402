"""Pytest configuration and fixtures"""

import pytest


@pytest.fixture
def sample_sql_queries():
    """Sample SQL queries for testing"""
    return {
        "valid_select": "SELECT ContractId, Title FROM view.Contract",
        "valid_with_where": "SELECT * FROM view.Contract WHERE SaveNo IS NOT NULL",
        "valid_with_join": """
            SELECT c.ContractId, p.Name
            FROM view.Contract c
            JOIN view.Partner p ON c.PartnerId = p.PartnerId
        """,
        "invalid_insert": "INSERT INTO view.Contract (Title) VALUES ('Test')",
        "invalid_delete": "DELETE FROM view.Contract WHERE ContractId = 1",
        "invalid_update": "UPDATE view.Contract SET Title = 'Test'",
        "invalid_drop": "DROP TABLE view.Contract",
        "invalid_table": "SELECT * FROM dbo.SomeTable",
        "invalid_exec": "EXEC sp_help",
        "with_comment": "SELECT * FROM view.Contract -- comment",
    }


@pytest.fixture
def allowed_views():
    """List of allowed views"""
    from mcp_server.database.allowed_views import ALLOWED_VIEWS
    return ALLOWED_VIEWS
