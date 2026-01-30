# ECS MCP Server - MCP 設計規格

> Resources、Tool、Prompts 設計規格

返回 [dev.md](dev.md)

---

## 設計原則

### 能力驅動架構

```
┌─────────────────────────────────────────────────────────────────┐
│                         用戶提問                                 │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI 讀取 Resources                                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │   Schema    │ │   Context   │ │  Reference  │               │
│  │ (資料結構)  │ │ (業務邏輯)  │ │  (對照表)   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI 規劃查詢步驟（可能需要多個 SQL）                              │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI 呼叫 Tool: query_database                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  安全查詢執行器                                          │   │
│  │  - 只允許 SELECT                                         │   │
│  │  - 只允許查詢白名單 View                                  │   │
│  │  - 限制回傳 1000 筆                                       │   │
│  │  - 記錄稽核日誌                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI 分析結果、匯總回答                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 三大功能分工

| 功能 | 職責 | 設計原則 |
|------|------|---------|
| **Resource** | 提供知識 | 豐富、完整、結構化 |
| **Tool** | 提供能力 | 精簡、安全、通用 |
| **Prompt** | 提供指引 | 框架化、可擴展 |

---

## Resources 設計

### Resource URI 結構

```
ecs://
├── schema/                 # 資料結構知識
│   ├── overview           # 資料庫概覽
│   ├── views              # View 清單與欄位
│   └── relationships      # 資料表關聯
│
├── context/               # 業務脈絡知識
│   ├── business-terms     # 業務術語定義
│   ├── contract-lifecycle # 合約生命週期
│   ├── approval-flow      # 審核流程
│   └── sla-definitions    # SLA 定義
│
├── reference/             # 對照表（動態）
│   ├── contract-types     # 合約類型
│   ├── departments        # 部門
│   ├── exam-stages        # 審核階段
│   └── currencies         # 幣別
│
└── stats/                 # 即時統計（動態）
    └── dashboard          # 系統儀表板
```

### Resource 類型說明

| 類型 | 說明 | 資料來源 |
|------|------|---------|
| **靜態** | 編譯時決定的內容 | 程式碼中的字串 |
| **動態** | 執行時從資料庫取得 | 內部 SQL 查詢（不經過 Tool） |

> **注意**：動態 Resource 的內部實作直接查詢資料庫，不經過 `query_database` Tool，因此可以查詢 `code.*` 等系統表。這是安全的，因為 Resource 只回傳預定義格式的資料。

---

### Schema Resources

#### ecs://schema/overview

```python
@mcp.resource("ecs://schema/overview")
def get_schema_overview() -> str:
    return """# ECS 資料庫概覽

## 基本資訊
- 資料庫：LT_ECS_LTCCore (SQL Server 2019)
- 資料表：187 個
- View：70 個
- Stored Procedure：504 個

## Schema 分布
| Schema | 數量 | 用途 |
|--------|------|------|
| code   | 37   | 代碼表（字典、配置） |
| data   | 39   | 業務數據（核心實體） |
| join   | 67   | 關聯表（多對多） |
| dbo    | 44   | 系統表、配置 |

## 可查詢的 View
AI 只能透過 `query_database` Tool 查詢 view.* 開頭的 View。
這些 View 已經做好欄位篩選、JOIN 組合、命名標準化。

詳細 View 清單請查閱 ecs://schema/views
"""
```

#### ecs://schema/views

回傳 View 白名單總覽與簡要說明。詳細欄位定義見 [dev-mcp-views.md](dev-mcp-views.md)。

```python
@mcp.resource("ecs://schema/views")
def get_schema_views() -> str:
    return """# 可查詢的 View 清單

## View 白名單（共 37 個）

### 合約核心
| View | 說明 |
|------|------|
| view.Contract | 合約主視圖 |
| view.ContractHistory | 審核歷程 |
| view.ContractExaminer | 審核人資訊 |
| view.ContractPartner | 合約相對人關聯 |
| view.ContractAttachment | 合約附件 |
| view.ContractExtendInfo | 合約擴展資訊 |
| view.ContractPriority | 合約優先權 |
| view.ContractFlowStageView | 流程階段視圖 |

### 相對人與組織
| View | 說明 |
|------|------|
| view.Partner | 相對人（客戶/供應商） |
| view.Department | 部門 |
| view.DepartmentTreeLevel | 部門樹狀結構 |

### 使用者與權限
| View | 說明 |
|------|------|
| view.User | 使用者 |
| view.UserAuthority | 使用者權限 |
| view.UserContractAuthority | 合約特許權限 |
| view.Role | 角色 |
| view.RoleAuthority | 角色權限 |

### 會辦與流程
| View | 說明 |
|------|------|
| view.OtherExaminer | 會辦審核人 |
| view.ExamStatus | 審核狀態 |

### 代理
| View | 說明 |
|------|------|
| view.Acting | 代理設定 |
| view.ActingAgent | 代理人 |
| view.ActingContract | 代理合約 |
| view.ActingEntry | 代理項目 |
| view.AllActing | 所有代理 |

### 關聯與事件
| View | 說明 |
|------|------|
| view.RelatedContract | 關聯合約 |
| view.Event | 事件 |
| view.EventAttachment | 事件附件 |
| view.EventContract | 事件合約 |
| view.AlertMailList | 警示郵件清單 |

### 其他
| View | 說明 |
|------|------|
| view.Project | 專案 |
| view.SignRequirement | 簽署需求 |
| view.UrgentLevel | 緊急程度 |
| view.MainContractType | 主合約類型 |
| view.SubContractType | 子合約類型 |
| view.Attachment | 附件 |
| view.LatestAttachment | 最新附件 |
| view.FileType | 檔案類型 |
| view.CombinedField | 組合欄位 |

---

## 重要欄位速查

### 判斷合約狀態
- `SaveNo IS NULL` → 進行中
- `SaveNo IS NOT NULL` → 已結案
- `CurrentStageId IS NOT NULL` → 審核中

### 合約分類
- `ContractCategoryId = 1` → 銷售（客戶合約）
- `ContractCategoryId = 2` → 採購（供應商合約）
- `ContractCategoryId = 3` → 其他

### 審核狀態
- `ExamStatusId = 1` → 通過
- `ExamStatusId = 2` → 退回
- `ExamStatusId = 3` → 審核中
- `ExamStatusId = 4` → 退件結案

### 會辦阻塞
- `Halt = 1 AND Replied = 0` → 阻塞中
"""
```

#### ecs://schema/relationships

```python
@mcp.resource("ecs://schema/relationships")
def get_schema_relationships() -> str:
    return """# 資料表關聯

## 核心關聯圖

```
Contract (合約)
    │
    ├── Partner (相對人)
    │   └── ContractPartner (多對多)
    │
    ├── Department (部門)
    │
    ├── ContractType (合約類型)
    │   └── MainContractType (主類型)
    │
    ├── ContractExaminer (審核人)
    │   ├── User (使用者)
    │   └── ExamStage (審核階段)
    │
    ├── ContractHistory (歷程)
    │   ├── User (審核人)
    │   └── ExamStatus (狀態)
    │
    ├── OtherExaminer (會辦)
    │   └── User (會辦人)
    │
    ├── RelatedContract (關聯合約)
    │
    └── ContractAttachment (附件)
```

## 主要 Foreign Key

| 子表 | 欄位 | 父表 | 欄位 |
|------|------|------|------|
| Contract | PartnerId | Partner | PartnerId |
| Contract | DepartmentId | Department | DepartmentId |
| Contract | ContractTypeId | ContractType | ContractTypeId |
| ContractHistory | ContractId | Contract | ContractId |
| ContractExaminer | ContractId | Contract | ContractId |
| OtherExaminer | ContractId | Contract | ContractId |
"""
```

---

### Context Resources

#### ecs://context/business-terms

```python
@mcp.resource("ecs://context/business-terms")
def get_business_terms() -> str:
    return """# 業務術語定義

## 合約分類

| 術語 | 定義 | SQL 判斷 |
|------|------|---------|
| **客戶合約** | 公司作為賣方 | `ContractCategoryId = 1` |
| **供應商合約** | 公司作為買方 | `ContractCategoryId = 2` |
| **其他合約** | 非交易性合約 | `ContractCategoryId = 3` |

## 合約狀態

| 術語 | 定義 | SQL 判斷 |
|------|------|---------|
| **進行中** | 尚未結案 | `SaveNo IS NULL` |
| **已結案** | 已歸檔 | `SaveNo IS NOT NULL` |
| **審核中** | 在流程中 | `SaveNo IS NULL AND CurrentStageId IS NOT NULL` |
| **已到期** | 到期日已過 | `ValidEndDate < GETDATE()` |
| **即將到期** | N 天內到期 | `ValidEndDate BETWEEN GETDATE() AND DATEADD(day, N, GETDATE())` |

## 關聯合約類型

| RelationType | 名稱 | 說明 |
|-------------:|------|------|
| 1 | 新增 | 全新合約 |
| 2 | 續約 | 延續既有合約 |
| 3 | 變更 | 修改條款 |
| 4 | 終止 | 提前終止 |

## 會辦狀態

| 術語 | SQL 判斷 |
|------|---------|
| **會辦阻塞** | `Halt = 1 AND Replied = 0` |
| **會辦完成** | `Replied = 1` |
| **會辦逾期** | `Halt = 1 AND Replied = 0 AND DATEDIFF(day, CreateDate, GETDATE()) > Deadline` |
"""
```

#### ecs://context/contract-lifecycle

```python
@mcp.resource("ecs://context/contract-lifecycle")
def get_contract_lifecycle() -> str:
    return """# 合約生命週期

## 標準流程

```
新增合約
    ↓
┌─────────────┐
│  申請人起案  │ ExamStageId = 1
└─────────────┘
    ↓
┌─────────────┐
│  主管審核    │ ExamStageId = 2
└─────────────┘
    ↓
┌─────────────┐
│  法務分案    │ ExamStageId = 3 (會簽)
└─────────────┘
    ↓
┌─────────────┐
│  法務審核    │ ExamStageId = 5
└─────────────┘
    ↓
┌─────────────┐
│ 法務主管審核 │ ExamStageId = 6
└─────────────┘
    ↓
┌─────────────┐
│  最終核准    │ ExamStageId = 7
└─────────────┘
    ↓
┌─────────────┐
│  簽署用印    │ ExamStageId = 8 或 51 (DocuSign)
└─────────────┘
    ↓
┌─────────────┐
│  結案歸檔    │ ExamStageId = 11
└─────────────┘
    ↓
  完成（SaveNo 有值）
```

## 會簽關卡

會簽 = 多人可同時審核，任一人通過即可。

**會簽階段 ID**：3, 8, 11, 12, 51
"""
```

#### ecs://context/approval-flow

```python
@mcp.resource("ecs://context/approval-flow")
def get_approval_flow() -> str:
    return """# 審核流程說明

## 審核階段清單

| ExamStageId | 代碼 | 名稱 |
|------------:|------|------|
| 1 | Applicant | 申請人 |
| 2 | DirectorApproval | 主管審核 |
| 3 | LegalAssignment | 法務分案 |
| 5 | LegalReview | 法務審核 |
| 6 | LegalDirectorReview | 法務主管審核 |
| 7 | FinalApproval | 最終核准 |
| 8 | Signing | 簽署用印 |
| 10 | CoExamination | 會辦審核 |
| 11 | ContractArchive | 結案歸檔 |
| 12 | ApplicantContractArchive | 申請人結案 |
| 16 | Withdrawn | 撤案 |
| 51 | Docusign | DocuSign |

## 退回機制

- 任何階段都可以退回到「申請人」階段
- 退回時需填寫原因（ExamMemo）
- 退回紀錄保存在 ContractHistory

## 會辦機制

| Halt | Replied | 狀態 |
|:----:|:-------:|------|
| 0 | - | 非必要會辦（FYI） |
| 1 | 0 | 必要會辦，尚未回覆（阻塞中） |
| 1 | 1 | 必要會辦，已回覆 |
"""
```

#### ecs://context/sla-definitions

```python
@mcp.resource("ecs://context/sla-definitions")
def get_sla_definitions() -> str:
    return """# SLA 定義

## 各階段標準處理天數

| 審核階段 | ExamStageId | 標準天數 |
|---------|------------:|--------:|
| 主管審核 | 2 | 3 天 |
| 法務分案 | 3 | 1 天 |
| 法務審核 | 5 | 5 天 |
| 法務主管審核 | 6 | 3 天 |
| 最終核准 | 7 | 5 天 |
| 簽署用印 | 8 | 3 天 |
| 會辦審核 | 10 | 7 天 |
| 結案歸檔 | 11 | 3 天 |

## 緊急程度調整

| UrgentLevel | 名稱 | SLA 調整 |
|------------:|------|---------|
| 1 | 一般 | 標準天數 |
| 2 | 急件 | 標準天數 × 0.5 |
| 3 | 特急 | 1 天 |

## 逾期判斷 SQL

```sql
-- 逾期案件（以法務審核為例，標準 5 天）
SELECT c.ContractId, c.Title,
       DATEDIFF(day, e.StayDate, GETDATE()) as DaysInStage
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL
  AND e.ExamStageId = 5
  AND e.ExamStatusId = 3
  AND DATEDIFF(day, e.StayDate, GETDATE()) > 5
```
"""
```

---

### Reference Resources（動態）

這些 Resource 從資料庫動態取得，內部直接查詢 `code.*` 表（不經過 `query_database` Tool）。

#### ecs://reference/contract-types

```python
@mcp.resource("ecs://reference/contract-types")
async def get_contract_types() -> str:
    """合約類型清單（從資料庫動態取得）"""
    # 內部實作，直接查詢 code.ContractType
    async with DatabasePool.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT ContractTypeId, ContractTypeName, ContractCategoryId
                FROM code.ContractType
                WHERE IsActive = 1
                ORDER BY ContractCategoryId, ContractTypeName
            """)
            rows = await cursor.fetchall()

    lines = ["# 合約類型清單\n"]
    lines.append("| ID | 名稱 | 分類 |")
    lines.append("|---:|------|------|")

    category_map = {1: "銷售", 2: "採購", 3: "其他"}
    for row in rows:
        cat = category_map.get(row[2], "未知")
        lines.append(f"| {row[0]} | {row[1]} | {cat} |")

    return "\n".join(lines)
```

#### ecs://reference/departments

```python
@mcp.resource("ecs://reference/departments")
async def get_departments() -> str:
    """部門清單"""
    async with DatabasePool.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT DepartmentId, DepartmentName, Level
                FROM view.Department
                WHERE IsActive = 1
                ORDER BY Level, DepartmentName
            """)
            rows = await cursor.fetchall()

    lines = ["# 部門清單\n"]
    lines.append("| ID | 名稱 | 層級 |")
    lines.append("|---:|------|-----:|")

    for row in rows:
        indent = "　" * (row[2] - 1) if row[2] else ""
        lines.append(f"| {row[0]} | {indent}{row[1]} | {row[2]} |")

    return "\n".join(lines)
```

#### ecs://reference/exam-stages

```python
@mcp.resource("ecs://reference/exam-stages")
async def get_exam_stages() -> str:
    """審核階段清單"""
    async with DatabasePool.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT ExamStageId, ExamStageName, ExamStageCode
                FROM code.ExamStage
                ORDER BY ExamStageId
            """)
            rows = await cursor.fetchall()

    lines = ["# 審核階段清單\n"]
    lines.append("| ID | 代碼 | 名稱 |")
    lines.append("|---:|------|------|")

    for row in rows:
        lines.append(f"| {row[0]} | {row[2]} | {row[1]} |")

    return "\n".join(lines)
```

#### ecs://reference/currencies

```python
@mcp.resource("ecs://reference/currencies")
async def get_currencies() -> str:
    """幣別清單"""
    async with DatabasePool.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT ExchangeTypeId, ExchangeName, ExchangeCode
                FROM code.ExchangeType
                ORDER BY ExchangeTypeId
            """)
            rows = await cursor.fetchall()

    lines = ["# 幣別清單\n"]
    lines.append("| ID | 代碼 | 名稱 |")
    lines.append("|---:|------|------|")

    for row in rows:
        lines.append(f"| {row[0]} | {row[2]} | {row[1]} |")

    return "\n".join(lines)
```

---

### Stats Resources（動態）

#### ecs://stats/dashboard

```python
@mcp.resource("ecs://stats/dashboard")
async def get_dashboard_stats() -> str:
    """系統儀表板統計"""
    async with DatabasePool.get_connection() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("""
                SELECT
                    (SELECT COUNT(*) FROM view.Contract WHERE SaveNo IS NULL) as ActiveCount,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE CreateDate >= DATEADD(month, -1, GETDATE())) as MonthlyNew,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE SaveNo IS NULL AND CurrentStageId IS NOT NULL) as PendingApproval,
                    (SELECT COUNT(*) FROM view.Contract
                     WHERE SaveNo IS NULL
                       AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 30, GETDATE())) as ExpiringSoon,
                    (SELECT COUNT(*) FROM view.OtherExaminer
                     WHERE Halt = 1 AND Replied = 0) as BlockedByCoExam
            """)
            row = await cursor.fetchone()

    from datetime import datetime
    return f"""# ECS 系統概況

> 更新時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

| 指標 | 數值 | 說明 |
|------|-----:|------|
| 進行中合約 | {row[0]:,} | SaveNo 為空 |
| 近一個月新增 | {row[1]:,} | 最近 30 天建立 |
| 待審核案件 | {row[2]:,} | 在審核流程中 |
| 30 天內到期 | {row[3]:,} | 需注意續約或結案 |
| 會辦阻塞中 | {row[4]:,} | Halt=1 且未回覆 |
"""
```

---

## Tool 設計

### query_database

這是 MCP Server **唯一的 Tool**，提供安全的 SQL 查詢能力。

```python
@mcp.tool()
async def query_database(
    sql: str,
    purpose: str
) -> dict:
    """
    執行唯讀 SQL 查詢

    Args:
        sql: SELECT 語句（只能查詢 view.* 開頭的 View）
        purpose: 查詢目的說明（用於稽核日誌）

    Returns:
        {
            "success": true,
            "columns": ["col1", "col2", ...],
            "rows": [[val1, val2, ...], ...],
            "row_count": 123,
            "truncated": false,
            "message": null
        }

    安全限制:
        - 只允許 SELECT 語句
        - 只能查詢 view.* 開頭的 View（共 37 個）
        - 回傳最多 1000 筆
        - 查詢 timeout 30 秒
        - 所有查詢記錄稽核日誌

    使用方式:
        1. 先讀取 ecs://schema/views 了解可用的 View
        2. 先讀取 ecs://context/business-terms 了解業務定義
        3. 撰寫 SELECT 語句（直接寫值，不支援參數化）
        4. 可多次呼叫，逐步分析複雜問題

    範例:
        query_database(
            sql=\"\"\"
                SELECT ContractId, Title, PartnerName, ValidEndDate
                FROM view.Contract
                WHERE SaveNo IS NULL
                  AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())
                ORDER BY ValidEndDate
            \"\"\",
            purpose="查詢 90 天內到期的進行中合約"
        )
    """
```

### 回傳格式

**成功**：

```json
{
    "success": true,
    "columns": ["ContractId", "Title", "ValidEndDate"],
    "rows": [
        [12345, "採購合約-台積電", "2024-03-15"],
        [12346, "服務合約-聯發科", "2024-03-20"]
    ],
    "row_count": 2,
    "truncated": false,
    "message": null
}
```

**失敗（安全錯誤）**：

```json
{
    "success": false,
    "columns": [],
    "rows": [],
    "row_count": 0,
    "truncated": false,
    "message": "安全錯誤：不允許查詢 data.Contract，只能查詢 view.* 開頭的授權 View"
}
```

**失敗（查詢錯誤）**：

```json
{
    "success": false,
    "columns": [],
    "rows": [],
    "row_count": 0,
    "truncated": false,
    "message": "查詢錯誤：Invalid column name 'Foo'"
}
```

**結果截斷**：

```json
{
    "success": true,
    "columns": ["ContractId", "Title"],
    "rows": [...],
    "row_count": 1000,
    "truncated": true,
    "message": "結果已截斷，僅顯示前 1000 筆。建議加入篩選條件縮小範圍。"
}
```

### 資料類型序列化

| SQL 類型 | Python 類型 | JSON 輸出 |
|---------|------------|----------|
| int, bigint | int | 數字 |
| decimal, money | str | 字串（避免精度問題） |
| datetime | str | ISO 8601 格式 |
| date | str | YYYY-MM-DD |
| bit | bool | true/false |
| nvarchar | str | 字串 |
| NULL | None | null |

---

## Prompts 設計

### data_analysis_guide

```python
@mcp.prompt()
def data_analysis_guide() -> str:
    """資料分析框架指引"""
    return """# ECS 合約資料分析指南

## Step 1: 理解問題

分析用戶問題的三個面向：
- **維度**：時間、部門、相對人、合約類型、幣別...
- **篩選**：日期範圍、金額範圍、狀態、特定對象...
- **輸出**：清單、統計、趨勢、比較...

## Step 2: 查閱背景知識

| 問題類型 | 建議讀取的 Resource |
|---------|-------------------|
| 需要了解欄位 | ecs://schema/views |
| 需要理解術語 | ecs://context/business-terms |
| 涉及審核流程 | ecs://context/approval-flow |
| 涉及 SLA/逾期 | ecs://context/sla-definitions |
| 需要代碼對照 | ecs://reference/* |

## Step 3: 規劃查詢步驟

複雜問題可能需要多個查詢：
1. 先取得基礎資料
2. 再做關聯或計算
3. 最後匯總分析

## Step 4: 執行查詢

- 每次查詢都明確說明 purpose
- 使用 ORDER BY 確保結果有意義
- 如結果被截斷，加入篩選條件

## Step 5: 匯總回答

- 整合多個查詢結果
- 提供分析洞察
- 標註資料時間點
"""
```

### common_queries

```python
@mcp.prompt()
def common_queries() -> str:
    """常見查詢範例"""
    return """# 常見查詢範例

## 到期預警
```sql
SELECT ContractId, Title, PartnerName, ValidEndDate,
       DATEDIFF(day, GETDATE(), ValidEndDate) as DaysUntilExpiry
FROM view.Contract
WHERE SaveNo IS NULL
  AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())
ORDER BY ValidEndDate
```

## 各部門合約金額統計
```sql
SELECT DepartmentName,
       COUNT(*) as ContractCount,
       SUM(Cost) as TotalAmount
FROM view.Contract
WHERE SaveNo IS NULL
GROUP BY DepartmentId, DepartmentName
ORDER BY TotalAmount DESC
```

## 審核效率統計
```sql
SELECT ExamStageName,
       COUNT(*) as CaseCount,
       AVG(DATEDIFF(day, StayDate, ExamDate)) as AvgDays
FROM view.ContractExaminer
WHERE ExamDate IS NOT NULL
  AND ExamDate >= DATEADD(month, -1, GETDATE())
GROUP BY ExamStageId, ExamStageName
ORDER BY ExamStageId
```

## 會辦阻塞案件
```sql
SELECT c.ContractId, c.Title, o.UserName, o.DepartmentName,
       DATEDIFF(day, o.CreateDate, GETDATE()) as WaitingDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
ORDER BY WaitingDays DESC
```

## 退回率統計
```sql
SELECT DepartmentName,
       COUNT(DISTINCT ContractId) as TotalCases,
       SUM(CASE WHEN ExamStatusId = 2 THEN 1 ELSE 0 END) as ReturnCount
FROM view.ContractHistory h
JOIN view.Contract c ON h.ContractId = c.ContractId
WHERE h.ExamDate >= DATEADD(month, -3, GETDATE())
GROUP BY c.DepartmentId, c.DepartmentName
```
"""
```

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [dev-mcp-views.md](dev-mcp-views.md) | 完整的 37 個 View 欄位說明 |
| [dev-infrastructure.md](dev-infrastructure.md) | 連線池、日誌、錯誤處理 |
| [dev-security.md](dev-security.md) | View 白名單、SQL 驗證、稽核 |
