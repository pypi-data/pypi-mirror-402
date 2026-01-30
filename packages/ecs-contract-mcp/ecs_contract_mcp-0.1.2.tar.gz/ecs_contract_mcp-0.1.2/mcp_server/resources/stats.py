"""Stats Resources - 即時統計（動態）

從資料庫動態取得系統統計資料：
- ecs://stats/dashboard - 系統儀表板統計
"""

from datetime import datetime

from mcp.server.fastmcp import FastMCP

from mcp_server.database.connection import DatabasePool
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)


def register_stats_resources(mcp: FastMCP) -> None:
    """註冊 Stats 相關 Resources"""

    @mcp.resource("ecs://stats/dashboard")
    async def get_dashboard_stats() -> str:
        """系統儀表板統計（從資料庫動態取得）"""
        try:
            # 取得各項統計數據
            columns, rows = await DatabasePool.execute_query("""
                SELECT
                    (SELECT COUNT(*) FROM view.Contract WHERE SaveNo IS NULL) as ActiveCount,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE CreateDate >= DATEADD(month, -1, GETDATE())) as MonthlyNew,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE SaveNo IS NULL AND CurrentStageId IS NOT NULL) as PendingApproval,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE SaveNo IS NULL
                       AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())) as ExpiringSoon30,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE SaveNo IS NULL
                       AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())) as ExpiringSoon90,
                    (SELECT COUNT(*) FROM view.OtherExaminer
                     WHERE Halt = 1 AND Replied = 0) as BlockedByCoExam
            """)

            if not rows:
                return "# ECS 系統概況\n\n> 無法取得統計資料"

            row = rows[0]
            active_count = row[0] or 0
            monthly_new = row[1] or 0
            pending_approval = row[2] or 0
            expiring_30 = row[3] or 0
            expiring_90 = row[4] or 0
            blocked = row[5] or 0

            # 取得各部門合約數量（前 10 名）
            _, dept_rows = await DatabasePool.execute_query("""
                SELECT TOP 10 DepartmentName, COUNT(*) as ContractCount
                FROM view.Contract
                WHERE SaveNo IS NULL
                GROUP BY DepartmentId, DepartmentName
                ORDER BY ContractCount DESC
            """)

            # 取得各審核階段待審數量
            _, stage_rows = await DatabasePool.execute_query("""
                SELECT e.ExamStageName, COUNT(*) as PendingCount
                FROM view.ContractExaminer e
                JOIN view.Contract c ON e.ContractId = c.ContractId
                WHERE c.SaveNo IS NULL AND e.ExamStatusId = 3
                GROUP BY e.ExamStageId, e.ExamStageName
                ORDER BY PendingCount DESC
            """)

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            lines = [
                "# ECS 系統概況",
                f"\n> 更新時間：{now}",
                "\n## 整體統計",
                "| 指標 | 數值 | 說明 |",
                "|------|-----:|------|",
                f"| 進行中合約 | {active_count:,} | SaveNo 為空 |",
                f"| 近一個月新增 | {monthly_new:,} | 最近 30 天建立 |",
                f"| 待審核案件 | {pending_approval:,} | 在審核流程中 |",
                f"| 30 天內到期 | {expiring_30:,} | 需注意續約或結案 |",
                f"| 90 天內到期 | {expiring_90:,} | 提前規劃續約 |",
                f"| 會辦阻塞中 | {blocked:,} | Halt=1 且未回覆 |",
            ]

            # 部門分布
            if dept_rows:
                lines.append("\n## 各部門進行中合約（前 10 名）")
                lines.append("| 部門 | 合約數 |")
                lines.append("|------|-------:|")
                for dept_row in dept_rows:
                    dept_name = dept_row[0] or "未知"
                    count = dept_row[1] or 0
                    lines.append(f"| {dept_name} | {count:,} |")

            # 審核階段分布
            if stage_rows:
                lines.append("\n## 各審核階段待審數量")
                lines.append("| 審核階段 | 待審數 |")
                lines.append("|----------|-------:|")
                for stage_row in stage_rows:
                    stage_name = stage_row[0] or "未知"
                    count = stage_row[1] or 0
                    lines.append(f"| {stage_name} | {count:,} |")

            return "\n".join(lines)

        except Exception as e:
            logger.error("stats_dashboard_error", error=str(e))
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return f"# ECS 系統概況\n\n> 更新時間：{now}\n\n> 無法取得統計資料：{e}"
