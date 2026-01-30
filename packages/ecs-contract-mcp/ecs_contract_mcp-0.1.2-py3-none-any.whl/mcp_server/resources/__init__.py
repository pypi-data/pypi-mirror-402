"""MCP Resources module

提供 AI 所需的背景知識，包含：

Schema Resources（靜態）:
- ecs://schema/overview - 資料庫概覽
- ecs://schema/views - View 清單與欄位說明
- ecs://schema/relationships - 資料表關聯

Context Resources（靜態）:
- ecs://context/business-terms - 業務術語定義
- ecs://context/contract-lifecycle - 合約生命週期
- ecs://context/approval-flow - 審核流程說明
- ecs://context/sla-definitions - SLA 定義

Reference Resources（動態）:
- ecs://reference/contract-types - 合約類型清單
- ecs://reference/departments - 部門清單
- ecs://reference/exam-stages - 審核階段清單
- ecs://reference/currencies - 幣別清單

Stats Resources（動態）:
- ecs://stats/dashboard - 系統儀表板統計
"""

from mcp.server.fastmcp import FastMCP

from mcp_server.resources.context import register_context_resources
from mcp_server.resources.reference import register_reference_resources
from mcp_server.resources.schema import register_schema_resources
from mcp_server.resources.stats import register_stats_resources


def register_resources(mcp: FastMCP) -> None:
    """註冊所有 MCP Resources

    Args:
        mcp: FastMCP server instance
    """
    # Schema Resources（靜態）
    register_schema_resources(mcp)

    # Context Resources（靜態）
    register_context_resources(mcp)

    # Reference Resources（動態，從資料庫取得）
    register_reference_resources(mcp)

    # Stats Resources（動態，從資料庫取得）
    register_stats_resources(mcp)


__all__ = ["register_resources"]
