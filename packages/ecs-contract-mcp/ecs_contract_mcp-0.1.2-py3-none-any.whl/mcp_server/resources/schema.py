"""Schema Resources - 資料結構知識

提供 AI 所需的資料庫 Schema 相關知識：
- ecs://schema/overview - 資料庫概覽
- ecs://schema/views - View 清單與欄位說明
- ecs://schema/relationships - 資料表關聯
"""

from mcp.server.fastmcp import FastMCP


def register_schema_resources(mcp: FastMCP) -> None:
    """註冊 Schema 相關 Resources"""

    @mcp.resource("ecs://schema/overview")
    def get_schema_overview() -> str:
        """資料庫概覽"""
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

    @mcp.resource("ecs://schema/views")
    def get_schema_views() -> str:
        """View 清單與欄位說明"""
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

## 主要 View 欄位速查

### view.Contract 主要欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID (PK) |
| ApplyNo | nvarchar | 申請號 |
| SaveNo | nvarchar | 結案號（NULL = 未結案） |
| Title | nvarchar | 合約標題 |
| PartnerId | int | 相對人 ID |
| PartnerName | nvarchar | 相對人名稱 |
| DepartmentId | int | 部門 ID |
| DepartmentName | nvarchar | 部門名稱 |
| ContractTypeId | int | 合約類型 ID |
| ContractTypeName | nvarchar | 合約類型名稱 |
| ContractCategoryId | int | 合約分類 (1=銷售, 2=採購, 3=其他) |
| Cost | decimal | 合約金額 |
| ExchangeTypeId | int | 幣別 ID |
| ExchangeName | nvarchar | 幣別名稱 |
| ValidStartDate | date | 生效日 |
| ValidEndDate | date | 到期日 |
| AutoExtend | bit | 是否自動展延 |
| CreateDate | datetime | 建立日期 |
| RecorderId | int | 申請人 ID |
| RecorderName | nvarchar | 申請人名稱 |
| CurrentStageId | int | 目前審核階段 ID |
| CurrentStageName | nvarchar | 目前審核階段名稱 |
| UrgentLevel | int | 緊急程度 (1=一般, 2=急件, 3=特急) |

### view.ContractHistory 主要欄位
| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractHistoryId | int | 歷程 ID (PK) |
| ContractId | int | 合約 ID |
| ExamStageId | int | 審核階段 ID |
| ExamStageName | nvarchar | 審核階段名稱 |
| ExamStatusId | int | 審核狀態 (1=通過, 2=退回, 3=審核中, 4=退件結案) |
| ExamStatusName | nvarchar | 審核狀態名稱 |
| ExamUserId | int | 審核人 ID |
| ExamUserName | nvarchar | 審核人名稱 |
| ExamDate | datetime | 審核日期 |
| ExamMemo | nvarchar | 審核意見 |

### view.OtherExaminer 主要欄位（會辦）
| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| UserId | int | 會辦人 ID |
| UserName | nvarchar | 會辦人名稱 |
| DepartmentName | nvarchar | 會辦人部門名稱 |
| Halt | bit | 是否必須回覆 (1=必須, 0=FYI) |
| Replied | bit | 是否已回覆 |
| Deadline | int | 期限天數 |
| CreateDate | datetime | 建立時間 |
| ReplyDate | datetime | 回覆時間 |
| ReplyMemo | nvarchar | 回覆內容 |

### view.User 主要欄位（使用者）
| 欄位 | 類型 | 說明 |
|------|------|------|
| UserID | int | 使用者 ID (PK) - 用於關聯其他表 |
| UserName | nvarchar | 姓名 |
| LoginID | nvarchar | 登入帳號 |
| UserDepartment | nvarchar | 部門名稱 |
| DepartmentID | int | 部門 ID |
| Title | nvarchar | 職稱 |
| UserEmail | nvarchar | 電子郵件 |
| UserExt | nvarchar | 分機 |
| Disable | bit | 是否停用 |

### view.ContractExaminer 主要欄位（審核人）
| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractID | int | 合約 ID |
| UserID | int | 審核人 ID - 對應 view.User.UserID |
| UserName | nvarchar | 審核人姓名 |
| ExamStage | nvarchar | 審核階段名稱 |
| ExamStatus | nvarchar | 審核狀態 |
| ExamResult | nvarchar | 審核結果 |
| AssignDate | datetime | 指派日期 |
| ExamDate | datetime | 審核日期 |
| ExamMemo | nvarchar | 審核意見 |

---

## ⚠️ 人員查詢最佳實踐

**查詢「某人在合約中的角色」時，必須用 UserID，不能用名字做 LIKE 搜尋！**

### 正確做法（三步驟）

**Step 1**: 先查 UserID
```sql
SELECT UserID, UserName, UserDepartment FROM [view].[User] WHERE UserName LIKE '%張三%'
-- 結果: UserID = 102
```

**Step 2**: 用 UserID 查詢角色統計
```sql
-- 作為合約承辦人
SELECT COUNT(*) FROM [view].[Contract] WHERE RecorderID = 102

-- 作為審查者（各階段分佈）
SELECT ExamStage, COUNT(*) FROM [view].[ContractExaminer] WHERE UserID = 102 GROUP BY ExamStage
```

**Step 3**: 如需明細，加 TOP 限制
```sql
SELECT TOP 5 ContractID, DocumentName, ExamStage FROM [view].[ContractExaminer] WHERE UserID = 102
```

### 錯誤做法（會超時或返回過多資料）
```sql
-- ❌ 不要這樣做！
SELECT * FROM [view].[Contract] WHERE RecorderName LIKE '%張三%' OR Examiners LIKE '%張三%'
```

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

    @mcp.resource("ecs://schema/relationships")
    def get_schema_relationships() -> str:
        """資料表關聯"""
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

## 常用 JOIN 模式

### 合約 + 相對人 + 部門
```sql
SELECT c.*, p.PartnerNo, p.TaxNo, d.DepartmentCode
FROM view.Contract c
LEFT JOIN view.Partner p ON c.PartnerId = p.PartnerId
LEFT JOIN view.Department d ON c.DepartmentId = d.DepartmentId
```

### 合約 + 審核歷程
```sql
SELECT c.ContractId, c.Title, h.*
FROM view.Contract c
JOIN view.ContractHistory h ON c.ContractId = h.ContractId
ORDER BY c.ContractId, h.ExamDate
```

### 合約 + 目前審核人
```sql
SELECT c.ContractId, c.Title, e.UserName as CurrentExaminer, e.ExamStageName
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL AND e.ExamStatusId = 3
```

### 合約 + 會辦狀態
```sql
SELECT c.ContractId, c.Title,
       COUNT(o.UserId) as TotalCoExam,
       SUM(CASE WHEN o.Replied = 1 THEN 1 ELSE 0 END) as Replied,
       SUM(CASE WHEN o.Halt = 1 AND o.Replied = 0 THEN 1 ELSE 0 END) as Blocking
FROM view.Contract c
LEFT JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE c.SaveNo IS NULL
GROUP BY c.ContractId, c.Title
HAVING SUM(CASE WHEN o.Halt = 1 AND o.Replied = 0 THEN 1 ELSE 0 END) > 0
```
"""
