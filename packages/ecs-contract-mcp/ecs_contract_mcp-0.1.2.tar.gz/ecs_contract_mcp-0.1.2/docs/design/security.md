# ECS MCP Server - 安全機制

> View 白名單、SQL 驗證、稽核日誌

返回 [dev.md](dev.md)

---

## 設計原則

本 MCP Server 採用 **單一系統帳號** 模式，不實作多用戶 Row-Level Security。

| 項目 | 決策 | 說明 |
|------|------|------|
| 認證模式 | 單一系統帳號 | 使用唯讀資料庫帳號 |
| 資料隔離 | 無 | 不實作 RLS |
| 稽核方式 | 日誌檔案 | 不新增資料庫表 |
| 資料遮罩 | 無 | 系統帳號可查看所有欄位 |

**安全防線**：
1. **View 白名單**：只允許查詢授權的 View
2. **SQL 驗證**：只允許 SELECT，禁止危險關鍵字
3. **結果限制**：最多回傳 1000 筆
4. **查詢 Timeout**：30 秒自動終止
5. **稽核日誌**：記錄所有查詢到日誌檔案

---

## View 白名單機制

### 白名單清單

白名單定義在 `database/allowed_views.py`，共 37 個 View。

> 完整清單見 [dev-mcp-views.md](dev-mcp-views.md)

```python
# database/allowed_views.py
"""View 白名單定義（單一資訊來源）"""

ALLOWED_VIEWS = [
    # 合約核心
    "view.Contract",
    "view.ContractAttachment",
    "view.ContractHistory",
    "view.ContractPartner",
    "view.ContractExaminer",
    "view.ContractExtendInfo",
    "view.ContractPriority",
    "view.ContractFlowStageView",
    # 相對人與組織
    "view.Partner",
    "view.Department",
    "view.DepartmentTreeLevel",
    # 使用者與權限
    "view.User",
    "view.UserAuthority",
    "view.UserContractAuthority",
    "view.Role",
    "view.RoleAuthority",
    # 會辦與流程
    "view.OtherExaminer",
    "view.ExamStatus",
    # 代理
    "view.Acting",
    "view.ActingAgent",
    "view.ActingContract",
    "view.ActingEntry",
    "view.AllActing",
    # 關聯與事件
    "view.RelatedContract",
    "view.Event",
    "view.EventAttachment",
    "view.EventContract",
    "view.AlertMailList",
    # 其他
    "view.Project",
    "view.SignRequirement",
    "view.UrgentLevel",
    "view.MainContractType",
    "view.SubContractType",
    "view.Attachment",
    "view.LatestAttachment",
    "view.FileType",
    "view.CombinedField",
]

# 轉為 set 加速查詢
ALLOWED_VIEWS_SET = set(ALLOWED_VIEWS)
```

```python
# database/query_executor.py
from database.allowed_views import ALLOWED_VIEWS_SET

# 使用時直接引用
if table not in ALLOWED_VIEWS_SET:
    raise SecurityError(...)
```

### 驗證邏輯

```python
def extract_tables_from_sql(sql: str) -> list[str]:
    """從 SQL 中提取資料表/View 名稱"""
    import re
    # 匹配 FROM 和 JOIN 後的表名
    pattern = r'\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)'
    matches = re.findall(pattern, sql, re.IGNORECASE)
    return list(set(matches))

def validate_tables(sql: str) -> None:
    """驗證 SQL 只查詢白名單內的 View"""
    tables = extract_tables_from_sql(sql)
    for table in tables:
        if table not in ALLOWED_VIEWS:
            raise SecurityError(
                f"不允許查詢 {table}，只能查詢 view.* 開頭的授權 View"
            )
```

---

## SQL 驗證機制

### 危險關鍵字檢查

```python
DANGEROUS_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE",
    "ALTER", "TRUNCATE", "EXEC", "EXECUTE", "sp_", "xp_",
    "GRANT", "REVOKE", "DENY", "BACKUP", "RESTORE",
    "SHUTDOWN", "DBCC", "BULK", "OPENROWSET", "OPENDATASOURCE"
]

def validate_sql(sql: str) -> None:
    """驗證 SQL 安全性"""
    sql_upper = sql.upper().strip()

    # 1. 只允許 SELECT
    if not sql_upper.startswith("SELECT"):
        raise SecurityError("只允許 SELECT 語句")

    # 2. 檢查危險關鍵字
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            raise SecurityError(f"不允許使用 {keyword}")

    # 3. 檢查註解（可能用於繞過檢查）
    if "--" in sql or "/*" in sql:
        raise SecurityError("不允許使用 SQL 註解")
```

### 結果限制

```python
MAX_ROWS = 1000

def enforce_row_limit(sql: str) -> str:
    """強制加入 TOP 限制"""
    import re
    sql_upper = sql.upper()
    if "TOP" not in sql_upper:
        sql = re.sub(
            r"^SELECT\s+",
            f"SELECT TOP {MAX_ROWS} ",
            sql,
            flags=re.IGNORECASE
        )
    return sql
```

---

## 稽核日誌

### 日誌格式

採用結構化 JSON 日誌，寫入檔案而非資料庫。

```python
# utils/audit.py
import structlog
from config import settings

# 設定稽核日誌
audit_logger = structlog.get_logger("audit")

def log_query(
    sql: str,
    purpose: str,
    row_count: int,
    execution_time_ms: int,
    success: bool,
    error: str = None
) -> None:
    """記錄查詢稽核日誌"""
    audit_logger.info(
        "query_executed",
        sql=sql,
        purpose=purpose,
        row_count=row_count,
        execution_time_ms=execution_time_ms,
        success=success,
        error=error
    )
```

### 日誌範例

```json
{
  "timestamp": "2024-01-21T10:30:00.123Z",
  "level": "info",
  "event": "query_executed",
  "sql": "SELECT TOP 1000 ContractId, Title FROM view.Contract WHERE SaveNo IS NULL",
  "purpose": "查詢進行中的合約清單",
  "row_count": 156,
  "execution_time_ms": 234,
  "success": true,
  "error": null
}
```

### 日誌輪替

建議使用外部工具（如 logrotate）進行日誌輪替：

```
# /etc/logrotate.d/ecs-mcp
/path/to/mcp_audit.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

---

## 安全檢查清單

### SQL Injection 防護

- [x] 只允許 SELECT 語句
- [x] 禁止危險關鍵字（INSERT/UPDATE/DELETE/DROP 等）
- [x] 禁止 SQL 註解
- [x] View 白名單驗證
- [ ] 考慮使用 sqlparse 做更嚴格的解析

### 查詢限制

- [x] 最多回傳 1000 筆
- [x] 查詢 timeout 30 秒
- [x] 強制加入 TOP 限制

### 稽核追蹤

- [x] 記錄所有查詢的 SQL
- [x] 記錄查詢目的
- [x] 記錄回傳筆數
- [x] 記錄執行時間
- [x] 記錄成功/失敗狀態

### 資料庫帳號

- [ ] 使用專用唯讀帳號
- [ ] 帳號只授權查詢 view.* 的權限
- [ ] 禁止存取其他 Schema

---

## 資料庫帳號設定建議

建議在 SQL Server 建立專用唯讀帳號：

```sql
-- 建立唯讀帳號
CREATE LOGIN mcp_readonly WITH PASSWORD = 'your_secure_password';
CREATE USER mcp_readonly FOR LOGIN mcp_readonly;

-- 只授權 view schema 的 SELECT 權限
GRANT SELECT ON SCHEMA::view TO mcp_readonly;

-- 拒絕其他權限
DENY INSERT, UPDATE, DELETE, EXECUTE ON DATABASE::LT_ECS_LTCCore TO mcp_readonly;
```

這樣即使應用層的 View 白名單被繞過，資料庫層也會阻擋非授權存取。
