"""Query database tool - the core tool for ECS MCP Server"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_server.database.query_executor import QueryExecutor
from mcp_server.utils.errors import DatabaseError, ErrorCode, SecurityError
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)


def serialize_value(value: Any) -> Any:
    """Serialize database value to JSON-compatible format

    Args:
        value: Database value to serialize

    Returns:
        JSON-serializable value
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def serialize_row(row: list[Any]) -> list[Any]:
    """Serialize a row of database values

    Args:
        row: Row of database values

    Returns:
        Row with all values serialized
    """
    return [serialize_value(v) for v in row]


def register_tools(mcp: FastMCP) -> None:
    """Register all tools with the MCP server

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.tool()
    async def query_database(sql: str, purpose: str) -> dict[str, Any]:
        """執行唯讀 SQL 查詢

        這是 ECS MCP Server 的核心查詢工具，提供安全的資料庫查詢能力。

        Args:
            sql: SELECT 語句（只能查詢 [view].* 開頭的 View，必須用方括號）
            purpose: 查詢目的說明（用於稽核日誌）

        Returns:
            查詢結果，包含：
            - success: 是否成功
            - columns: 欄位名稱列表
            - rows: 資料列（二維陣列）
            - row_count: 回傳筆數
            - truncated: 是否被截斷
            - message: 錯誤或警告訊息

        安全限制:
            - 只允許 SELECT 語句
            - 只能查詢 [view].* 開頭的 View（共 37 個）
            - 回傳最多 1000 筆
            - 查詢 timeout 30 秒
            - 所有查詢記錄稽核日誌

        ⚠️ 效能警告 - 人員查詢必讀:
            查詢「某人在合約中的角色」時，絕對不要用名字做 LIKE 搜尋！
            這會導致查詢超時或返回過多資料。

            ❌ 錯誤做法（會超時）:
            SELECT * FROM [view].[Contract]
            WHERE RecorderName LIKE '%張三%' OR Examiners LIKE '%張三%'

            ✅ 正確做法（先查 UserID，再用 ID 查詢）:
            Step 1: SELECT UserID, UserName FROM [view].[User] WHERE UserName LIKE '%張三%'
            Step 2: SELECT COUNT(*) FROM [view].[Contract] WHERE RecorderID = 102
            Step 3: SELECT ExamStage, COUNT(*) FROM [view].[ContractExaminer] WHERE UserID = 102 GROUP BY ExamStage

        使用方式:
            1. View 名稱必須用方括號：[view].[Contract]，不能寫 view.Contract
            2. 人員查詢：先查 [view].[User] 取得 UserID，再用 ID 查其他表
            3. 優先返回統計：用 COUNT(*) 和 GROUP BY，避免返回大量明細
            4. 可多次呼叫，逐步分析複雜問題

        範例:
            query_database(
                sql=\"\"\"
                    SELECT ContractId, DocumentName, Partners, ValidEndDate
                    FROM [view].[Contract]
                    WHERE SaveNo IS NULL
                      AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())
                    ORDER BY ValidEndDate
                \"\"\",
                purpose="查詢 90 天內到期的進行中合約"
            )
        """
        logger.info(
            "query_database_called",
            purpose=purpose,
            sql_length=len(sql),
        )

        try:
            # Execute query through secure executor
            result = await QueryExecutor.execute(
                sql=sql,
                purpose=purpose,
            )

            # Serialize rows for JSON output
            serialized_rows = [serialize_row(row) for row in result.rows]

            response: dict[str, Any] = {
                "success": True,
                "columns": result.columns,
                "rows": serialized_rows,
                "row_count": result.row_count,
                "truncated": result.truncated,
                "message": None,
            }

            if result.truncated:
                response["message"] = (
                    f"結果已截斷，僅顯示前 {result.row_count} 筆。"
                    "建議加入篩選條件縮小範圍。"
                )

            logger.info(
                "query_database_success",
                purpose=purpose,
                row_count=result.row_count,
                truncated=result.truncated,
                execution_time_ms=result.execution_time_ms,
            )

            return response

        except SecurityError as e:
            logger.warning(
                "query_database_security_error",
                purpose=purpose,
                error_code=e.code.value,
                error_message=e.message,
            )
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "message": f"安全錯誤：{e.message}",
            }

        except DatabaseError as e:
            logger.error(
                "query_database_db_error",
                purpose=purpose,
                error_code=e.code.value,
                error_message=e.message,
            )
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "message": f"資料庫錯誤：{e.message}",
            }

        except Exception as e:
            logger.exception(
                "query_database_unexpected_error",
                purpose=purpose,
                error=str(e),
            )
            return {
                "success": False,
                "columns": [],
                "rows": [],
                "row_count": 0,
                "truncated": False,
                "message": f"查詢錯誤：{str(e)}",
            }
