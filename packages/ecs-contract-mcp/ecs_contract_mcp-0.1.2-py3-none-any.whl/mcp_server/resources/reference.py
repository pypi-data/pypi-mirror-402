"""Reference Resources - 對照表（動態）

從資料庫動態取得對照表資料：
- ecs://reference/contract-types - 合約類型清單
- ecs://reference/departments - 部門清單
- ecs://reference/exam-stages - 審核階段清單
- ecs://reference/currencies - 幣別清單

注意：這些 Resource 內部直接查詢 code.* 表，不經過 query_database Tool。
這是安全的，因為 Resource 只回傳預定義格式的資料。
"""

from mcp.server.fastmcp import FastMCP

from mcp_server.database.connection import DatabasePool
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)


def register_reference_resources(mcp: FastMCP) -> None:
    """註冊 Reference 相關 Resources"""

    @mcp.resource("ecs://reference/contract-types")
    async def get_contract_types() -> str:
        """合約類型清單（從資料庫動態取得）"""
        try:
            columns, rows = await DatabasePool.execute_query("""
                SELECT ContractTypeId, ContractTypeName, ContractCategoryId
                FROM code.ContractType
                WHERE IsActive = 1
                ORDER BY ContractCategoryId, ContractTypeName
            """)

            lines = ["# 合約類型清單\n"]
            lines.append("| ID | 名稱 | 分類 |")
            lines.append("|---:|------|------|")

            category_map = {1: "銷售", 2: "採購", 3: "其他"}
            for row in rows:
                type_id, type_name, category_id = row[0], row[1], row[2]
                cat = category_map.get(category_id, "未知")
                lines.append(f"| {type_id} | {type_name} | {cat} |")

            lines.append(f"\n> 共 {len(rows)} 個合約類型")
            return "\n".join(lines)

        except Exception as e:
            logger.error("reference_contract_types_error", error=str(e))
            return f"# 合約類型清單\n\n> 無法取得資料：{e}"

    @mcp.resource("ecs://reference/departments")
    async def get_departments() -> str:
        """部門清單（從資料庫動態取得）"""
        try:
            columns, rows = await DatabasePool.execute_query("""
                SELECT DepartmentId, DepartmentName, DepartmentCode, Level
                FROM view.Department
                WHERE IsActive = 1
                ORDER BY Level, DepartmentName
            """)

            lines = ["# 部門清單\n"]
            lines.append("| ID | 代碼 | 名稱 | 層級 |")
            lines.append("|---:|------|------|-----:|")

            for row in rows:
                dept_id, dept_name, dept_code, level = row[0], row[1], row[2], row[3]
                # 用全形空白做層級縮排
                indent = "\u3000" * ((level or 1) - 1)
                code_str = dept_code or ""
                lines.append(f"| {dept_id} | {code_str} | {indent}{dept_name} | {level or 1} |")

            lines.append(f"\n> 共 {len(rows)} 個部門")
            return "\n".join(lines)

        except Exception as e:
            logger.error("reference_departments_error", error=str(e))
            return f"# 部門清單\n\n> 無法取得資料：{e}"

    @mcp.resource("ecs://reference/exam-stages")
    async def get_exam_stages() -> str:
        """審核階段清單（從資料庫動態取得）"""
        try:
            columns, rows = await DatabasePool.execute_query("""
                SELECT ExamStageId, ExamStageName, ExamStageCode
                FROM code.ExamStage
                ORDER BY ExamStageId
            """)

            lines = ["# 審核階段清單\n"]
            lines.append("| ID | 代碼 | 名稱 |")
            lines.append("|---:|------|------|")

            for row in rows:
                stage_id, stage_name, stage_code = row[0], row[1], row[2]
                code_str = stage_code or ""
                lines.append(f"| {stage_id} | {code_str} | {stage_name} |")

            lines.append(f"\n> 共 {len(rows)} 個審核階段")

            # 附加說明
            lines.append("\n## 常用階段說明")
            lines.append("| ID | 說明 |")
            lines.append("|---:|------|")
            lines.append("| 1 | 申請人起案 |")
            lines.append("| 2 | 主管審核 |")
            lines.append("| 3 | 法務分案（會簽） |")
            lines.append("| 5 | 法務審核 |")
            lines.append("| 6 | 法務主管審核 |")
            lines.append("| 7 | 最終核准 |")
            lines.append("| 8 | 簽署用印（會簽） |")
            lines.append("| 10 | 會辦審核 |")
            lines.append("| 11 | 結案歸檔（會簽） |")
            lines.append("| 16 | 撤案 |")
            lines.append("| 51 | DocuSign 電子簽章 |")

            return "\n".join(lines)

        except Exception as e:
            logger.error("reference_exam_stages_error", error=str(e))
            return f"# 審核階段清單\n\n> 無法取得資料：{e}"

    @mcp.resource("ecs://reference/currencies")
    async def get_currencies() -> str:
        """幣別清單（從資料庫動態取得）"""
        try:
            columns, rows = await DatabasePool.execute_query("""
                SELECT ExchangeTypeId, ExchangeName, ExchangeCode
                FROM code.ExchangeType
                ORDER BY ExchangeTypeId
            """)

            lines = ["# 幣別清單\n"]
            lines.append("| ID | 代碼 | 名稱 |")
            lines.append("|---:|------|------|")

            for row in rows:
                type_id, name, code = row[0], row[1], row[2]
                code_str = code or ""
                name_str = name or ""
                lines.append(f"| {type_id} | {code_str} | {name_str} |")

            lines.append(f"\n> 共 {len(rows)} 種幣別")

            return "\n".join(lines)

        except Exception as e:
            logger.error("reference_currencies_error", error=str(e))
            return f"# 幣別清單\n\n> 無法取得資料：{e}"
