# ECS MCP Server - View 欄位說明

> 完整的 37 個可查詢 View 欄位定義

返回 [dev-mcp-design.md](dev-mcp-design.md)

---

## View 白名單總覽

| 類別 | View 名稱 | 說明 |
|------|----------|------|
| **合約核心** | view.Contract | 合約主視圖 |
| | view.ContractHistory | 審核歷程 |
| | view.ContractExaminer | 審核人資訊 |
| | view.ContractPartner | 合約相對人關聯 |
| | view.ContractAttachment | 合約附件 |
| | view.ContractExtendInfo | 合約擴展資訊 |
| | view.ContractPriority | 合約優先權 |
| | view.ContractFlowStageView | 流程階段視圖 |
| **相對人** | view.Partner | 相對人（客戶/供應商） |
| **組織** | view.Department | 部門 |
| | view.DepartmentTreeLevel | 部門樹狀結構 |
| **使用者** | view.User | 使用者 |
| | view.UserAuthority | 使用者權限 |
| | view.UserContractAuthority | 合約特許權限 |
| | view.Role | 角色 |
| | view.RoleAuthority | 角色權限 |
| **會辦** | view.OtherExaminer | 會辦審核人 |
| **流程** | view.ExamStatus | 審核狀態 |
| **代理** | view.Acting | 代理設定 |
| | view.ActingAgent | 代理人 |
| | view.ActingContract | 代理合約 |
| | view.ActingEntry | 代理項目 |
| | view.AllActing | 所有代理 |
| **關聯合約** | view.RelatedContract | 關聯合約 |
| **事件/通知** | view.Event | 事件 |
| | view.EventAttachment | 事件附件 |
| | view.EventContract | 事件合約 |
| | view.AlertMailList | 警示郵件清單 |
| **其他** | view.Project | 專案 |
| | view.SignRequirement | 簽署需求 |
| | view.UrgentLevel | 緊急程度 |
| | view.MainContractType | 主合約類型 |
| | view.SubContractType | 子合約類型 |
| | view.Attachment | 附件 |
| | view.LatestAttachment | 最新附件 |
| | view.FileType | 檔案類型 |
| | view.CombinedField | 組合欄位 |

---

## 合約核心 Views

### view.Contract

合約主視圖，包含完整的合約基本資訊與關聯名稱。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID (PK) |
| ApplyNo | nvarchar | 申請號 |
| SaveNo | nvarchar | 結案號（NULL = 未結案） |
| Title | nvarchar | 合約標題 |
| PartnerId | int | 相對人 ID (FK) |
| PartnerName | nvarchar | 相對人名稱 |
| DepartmentId | int | 部門 ID (FK) |
| DepartmentName | nvarchar | 部門名稱 |
| ContractTypeId | int | 合約類型 ID (FK) |
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

**常用查詢模式**：

```sql
-- 進行中的合約
SELECT * FROM view.Contract WHERE SaveNo IS NULL

-- 已結案的合約
SELECT * FROM view.Contract WHERE SaveNo IS NOT NULL

-- 特定部門的合約
SELECT * FROM view.Contract WHERE DepartmentId = 5

-- 即將到期的合約（90 天內）
SELECT ContractId, Title, PartnerName, ValidEndDate,
       DATEDIFF(day, GETDATE(), ValidEndDate) as DaysUntilExpiry
FROM view.Contract
WHERE SaveNo IS NULL
  AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())
ORDER BY ValidEndDate

-- 特定相對人的合約
SELECT * FROM view.Contract WHERE PartnerName LIKE '%台積電%'
```

---

### view.ContractHistory

合約審核歷程，記錄每次審核動作。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractHistoryId | int | 歷程 ID (PK) |
| ContractId | int | 合約 ID (FK) |
| ExamStageId | int | 審核階段 ID |
| ExamStageName | nvarchar | 審核階段名稱 |
| ExamStatusId | int | 審核狀態 (1=通過, 2=退回, 3=審核中, 4=退件結案) |
| ExamStatusName | nvarchar | 審核狀態名稱 |
| ExamUserId | int | 審核人 ID |
| ExamUserName | nvarchar | 審核人名稱 |
| ExamDate | datetime | 審核日期 |
| ExamMemo | nvarchar | 審核意見 |

**常用查詢模式**：

```sql
-- 特定合約的完整審核歷程
SELECT * FROM view.ContractHistory
WHERE ContractId = 12345
ORDER BY ExamDate

-- 退回紀錄（含原因）
SELECT ContractId, ExamStageName, ExamUserName, ExamMemo, ExamDate
FROM view.ContractHistory
WHERE ExamStatusId = 2
ORDER BY ExamDate DESC

-- 各階段審核次數統計
SELECT ExamStageName, COUNT(*) as Count
FROM view.ContractHistory
WHERE ExamDate >= DATEADD(month, -1, GETDATE())
GROUP BY ExamStageId, ExamStageName
ORDER BY Count DESC
```

---

### view.ContractExaminer

合約審核人資訊，記錄每個階段的審核人與狀態。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| ExamStageId | int | 審核階段 ID |
| ExamStageName | nvarchar | 審核階段名稱 |
| UserId | int | 審核人 ID |
| UserName | nvarchar | 審核人名稱 |
| ExamStatusId | int | 審核狀態 |
| StayDate | datetime | 進入此階段的時間 |
| ExamDate | datetime | 審核完成時間（NULL = 尚未審核） |

**常用查詢模式**：

```sql
-- 目前待審核的案件（各審核人）
SELECT e.UserName, COUNT(*) as PendingCount
FROM view.ContractExaminer e
JOIN view.Contract c ON e.ContractId = c.ContractId
WHERE c.SaveNo IS NULL AND e.ExamStatusId = 3
GROUP BY e.UserId, e.UserName
ORDER BY PendingCount DESC

-- 計算各階段滯留天數
SELECT ContractId, ExamStageName,
       DATEDIFF(day, StayDate, ISNULL(ExamDate, GETDATE())) as DaysInStage
FROM view.ContractExaminer
WHERE ExamStatusId = 3

-- 審核效率統計（各階段平均天數）
SELECT ExamStageName,
       COUNT(*) as CaseCount,
       AVG(DATEDIFF(day, StayDate, ExamDate)) as AvgDays,
       MAX(DATEDIFF(day, StayDate, ExamDate)) as MaxDays
FROM view.ContractExaminer
WHERE ExamDate IS NOT NULL
  AND ExamDate >= DATEADD(month, -3, GETDATE())
GROUP BY ExamStageId, ExamStageName
ORDER BY ExamStageId
```

---

### view.ContractPartner

合約與相對人的關聯（支援多相對人）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| PartnerId | int | 相對人 ID |
| PartnerName | nvarchar | 相對人名稱 |
| IsPrimary | bit | 是否為主要相對人 |

**常用查詢模式**：

```sql
-- 合約的所有相對人
SELECT * FROM view.ContractPartner WHERE ContractId = 12345

-- 有多個相對人的合約
SELECT ContractId, COUNT(*) as PartnerCount
FROM view.ContractPartner
GROUP BY ContractId
HAVING COUNT(*) > 1
```

---

### view.ContractAttachment

合約附件資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| AttachmentId | int | 附件 ID (PK) |
| ContractId | int | 合約 ID (FK) |
| FileName | nvarchar | 檔案名稱 |
| FileTypeId | int | 檔案類型 ID |
| FileTypeName | nvarchar | 檔案類型名稱 |
| FileSize | bigint | 檔案大小（bytes） |
| UploadDate | datetime | 上傳日期 |
| UploadUserId | int | 上傳者 ID |
| UploadUserName | nvarchar | 上傳者名稱 |

**常用查詢模式**：

```sql
-- 合約的所有附件
SELECT * FROM view.ContractAttachment WHERE ContractId = 12345

-- 缺少正式合約文件的進行中案件
SELECT c.ContractId, c.Title
FROM view.Contract c
LEFT JOIN view.ContractAttachment a
  ON c.ContractId = a.ContractId AND a.FileTypeId = 1  -- 假設 1 = 正式合約
WHERE c.SaveNo IS NULL AND a.AttachmentId IS NULL
```

---

### view.ContractExtendInfo

合約擴展資訊（自定義欄位）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| FieldName | nvarchar | 欄位名稱 |
| FieldValue | nvarchar | 欄位值 |
| FieldType | nvarchar | 欄位類型 |

---

### view.ContractPriority

合約優先權設定。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| PriorityId | int | 優先權 ID |
| PriorityName | nvarchar | 優先權名稱 |
| PriorityDate | date | 優先權日期 |
| PriorityNo | nvarchar | 優先權號碼 |
| Country | nvarchar | 國家 |

---

### view.ContractFlowStageView

合約流程階段視圖。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| FlowId | int | 流程 ID |
| FlowName | nvarchar | 流程名稱 |
| StageId | int | 階段 ID |
| StageName | nvarchar | 階段名稱 |
| StageOrder | int | 階段順序 |
| IsCurrentStage | bit | 是否為目前階段 |

---

## 相對人 Views

### view.Partner

相對人（客戶/供應商）資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| PartnerId | int | 相對人 ID (PK) |
| PartnerName | nvarchar | 相對人名稱 |
| PartnerNo | nvarchar | 相對人編號 |
| TaxNo | nvarchar | 統一編號 |
| Address | nvarchar | 地址 |
| ContactName | nvarchar | 聯絡人 |
| ContactPhone | nvarchar | 聯絡電話 |
| ContactEmail | nvarchar | 聯絡信箱 |
| IsActive | bit | 是否啟用 |

**常用查詢模式**：

```sql
-- 搜尋相對人
SELECT * FROM view.Partner WHERE PartnerName LIKE '%科技%'

-- 相對人的合約統計
SELECT p.PartnerId, p.PartnerName,
       COUNT(c.ContractId) as ContractCount,
       SUM(c.Cost) as TotalAmount
FROM view.Partner p
LEFT JOIN view.Contract c ON p.PartnerId = c.PartnerId
GROUP BY p.PartnerId, p.PartnerName
ORDER BY ContractCount DESC
```

---

## 組織 Views

### view.Department

部門資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| DepartmentId | int | 部門 ID (PK) |
| DepartmentName | nvarchar | 部門名稱 |
| DepartmentCode | nvarchar | 部門代碼 |
| ParentId | int | 上級部門 ID |
| Level | int | 層級（1=最高層） |
| IsActive | bit | 是否啟用 |

**常用查詢模式**：

```sql
-- 部門清單（含層級縮排）
SELECT DepartmentId,
       REPLICATE('　', Level - 1) + DepartmentName as DepartmentName,
       Level
FROM view.Department
WHERE IsActive = 1
ORDER BY Level, DepartmentName

-- 各部門合約數量
SELECT d.DepartmentName, COUNT(c.ContractId) as ContractCount
FROM view.Department d
LEFT JOIN view.Contract c ON d.DepartmentId = c.DepartmentId
WHERE d.IsActive = 1
GROUP BY d.DepartmentId, d.DepartmentName
ORDER BY ContractCount DESC
```

---

### view.DepartmentTreeLevel

部門樹狀結構（含完整路徑）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| DepartmentId | int | 部門 ID |
| DepartmentName | nvarchar | 部門名稱 |
| FullPath | nvarchar | 完整路徑（如：總公司/事業群/部門） |
| Level | int | 層級 |
| RootId | int | 根部門 ID |

---

## 使用者 Views

### view.User

使用者資訊（已遮蔽敏感欄位如密碼、身分證字號）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| UserId | int | 使用者 ID (PK) |
| UserName | nvarchar | 姓名 |
| EmployeeNo | nvarchar | 員工編號 |
| Email | nvarchar | 電子郵件 |
| DepartmentId | int | 部門 ID |
| DepartmentName | nvarchar | 部門名稱 |
| PositionLevel | int | 職級 |
| IsActive | bit | 是否在職 |

**常用查詢模式**：

```sql
-- 搜尋使用者
SELECT * FROM view.User WHERE UserName LIKE '%王%'

-- 特定部門的使用者
SELECT * FROM view.User WHERE DepartmentId = 5 AND IsActive = 1
```

---

### view.UserAuthority

使用者權限設定。

| 欄位 | 類型 | 說明 |
|------|------|------|
| UserId | int | 使用者 ID |
| UserName | nvarchar | 使用者名稱 |
| AuthorityId | int | 權限 ID |
| AuthorityName | nvarchar | 權限名稱 |
| AuthorityCode | nvarchar | 權限代碼 |

---

### view.UserContractAuthority

使用者合約特許權限（個別合約的額外授權）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| UserId | int | 被授權的使用者 ID |
| UserName | nvarchar | 使用者名稱 |
| GrantUserId | int | 授權人 ID |
| GrantUserName | nvarchar | 授權人名稱 |
| GrantDate | datetime | 授權日期 |
| AuthorityType | int | 權限類型 (1=檢視, 2=編輯) |

**常用查詢模式**：

```sql
-- 特許權限授予紀錄（稽核用）
SELECT ContractId, UserName, GrantUserName, GrantDate, AuthorityType
FROM view.UserContractAuthority
WHERE GrantDate >= DATEADD(month, -6, GETDATE())
ORDER BY GrantDate DESC
```

---

### view.Role

角色定義。

| 欄位 | 類型 | 說明 |
|------|------|------|
| RoleId | int | 角色 ID (PK) |
| RoleName | nvarchar | 角色名稱 |
| RoleCode | nvarchar | 角色代碼 |
| Description | nvarchar | 說明 |
| IsActive | bit | 是否啟用 |

---

### view.RoleAuthority

角色權限對應。

| 欄位 | 類型 | 說明 |
|------|------|------|
| RoleId | int | 角色 ID |
| RoleName | nvarchar | 角色名稱 |
| AuthorityId | int | 權限 ID |
| AuthorityName | nvarchar | 權限名稱 |
| AuthorityCode | nvarchar | 權限代碼 |

---

## 會辦 Views

### view.OtherExaminer

會辦審核人資訊（跨部門徵詢）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| UserId | int | 會辦人 ID |
| UserName | nvarchar | 會辦人名稱 |
| DepartmentId | int | 會辦人部門 ID |
| DepartmentName | nvarchar | 會辦人部門名稱 |
| Halt | bit | 是否必須回覆 (1=必須, 0=FYI) |
| Replied | bit | 是否已回覆 |
| Deadline | int | 期限天數 |
| CreateDate | datetime | 建立時間 |
| ReplyDate | datetime | 回覆時間 |
| ReplyMemo | nvarchar | 回覆內容 |

**常用查詢模式**：

```sql
-- 會辦阻塞案件（必須回覆但尚未回覆）
SELECT c.ContractId, c.Title, o.UserName, o.DepartmentName,
       DATEDIFF(day, o.CreateDate, GETDATE()) as WaitingDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
ORDER BY WaitingDays DESC

-- 會辦逾期案件
SELECT c.ContractId, c.Title, o.UserName, o.Deadline,
       DATEDIFF(day, o.CreateDate, GETDATE()) as ActualDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
  AND DATEDIFF(day, o.CreateDate, GETDATE()) > o.Deadline
ORDER BY ActualDays DESC

-- 會辦回覆統計（各部門）
SELECT o.DepartmentName,
       COUNT(*) as TotalRequests,
       SUM(CASE WHEN o.Replied = 1 THEN 1 ELSE 0 END) as Replied,
       AVG(CASE WHEN o.Replied = 1
           THEN DATEDIFF(day, o.CreateDate, o.ReplyDate)
           ELSE NULL END) as AvgReplyDays
FROM view.OtherExaminer o
WHERE o.CreateDate >= DATEADD(month, -3, GETDATE())
GROUP BY o.DepartmentId, o.DepartmentName
ORDER BY TotalRequests DESC
```

---

## 流程 Views

### view.ExamStatus

審核狀態定義。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ExamStatusId | int | 狀態 ID (PK) |
| ExamStatusName | nvarchar | 狀態名稱 |
| ExamStatusCode | nvarchar | 狀態代碼 |

**狀態對照**：

| ID | 名稱 | 說明 |
|---:|------|------|
| 1 | 通過 | 審核通過，進入下一階段 |
| 2 | 退回 | 退回修改 |
| 3 | 審核中 | 等待審核 |
| 4 | 退件結案 | 拒絕並終止 |

---

## 代理 Views

### view.Acting

代理設定主表。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ActingId | int | 代理 ID (PK) |
| UserId | int | 被代理人 ID |
| UserName | nvarchar | 被代理人名稱 |
| AgentId | int | 代理人 ID |
| AgentName | nvarchar | 代理人名稱 |
| StartDate | date | 代理開始日 |
| EndDate | date | 代理結束日 |
| IsActive | bit | 是否啟用 |

---

### view.ActingAgent

代理人資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ActingId | int | 代理 ID |
| AgentId | int | 代理人 ID |
| AgentName | nvarchar | 代理人名稱 |
| AgentDepartment | nvarchar | 代理人部門 |

---

### view.ActingContract

被代理的合約。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ActingId | int | 代理 ID |
| ContractId | int | 合約 ID |
| ContractTitle | nvarchar | 合約標題 |

---

### view.ActingEntry

代理項目（代理的權限範圍）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ActingId | int | 代理 ID |
| EntryType | nvarchar | 項目類型 |
| EntryId | int | 項目 ID |
| EntryName | nvarchar | 項目名稱 |

---

### view.AllActing

所有代理資訊（綜合視圖）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ActingId | int | 代理 ID |
| UserId | int | 被代理人 ID |
| UserName | nvarchar | 被代理人名稱 |
| AgentId | int | 代理人 ID |
| AgentName | nvarchar | 代理人名稱 |
| StartDate | date | 開始日 |
| EndDate | date | 結束日 |
| ActingType | nvarchar | 代理類型 |

---

## 關聯合約 Views

### view.RelatedContract

關聯合約資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 主合約 ID |
| RelatedContractId | int | 被關聯的合約 ID |
| RelatedTitle | nvarchar | 被關聯合約標題 |
| RelationType | int | 關聯類型 |
| RelationTypeName | nvarchar | 關聯類型名稱 |

**關聯類型對照**：

| ID | 名稱 | 說明 |
|---:|------|------|
| 1 | 新增 | 全新合約 |
| 2 | 續約 | 延續既有合約 |
| 3 | 變更 | 修改既有合約條款 |
| 4 | 終止 | 提前終止合約 |

**常用查詢模式**：

```sql
-- 查詢續約關係
SELECT c.ContractId, c.Title, r.RelatedTitle as OriginalContract
FROM view.Contract c
JOIN view.RelatedContract r ON c.ContractId = r.ContractId
WHERE r.RelationType = 2

-- 續約率分析
WITH Expired AS (
    SELECT ContractId FROM view.Contract
    WHERE YEAR(ValidEndDate) = YEAR(GETDATE()) - 1
)
SELECT
    COUNT(*) as TotalExpired,
    SUM(CASE WHEN r.RelatedContractId IS NOT NULL THEN 1 ELSE 0 END) as Renewed,
    CAST(SUM(CASE WHEN r.RelatedContractId IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT)
        / COUNT(*) as RenewalRate
FROM Expired e
LEFT JOIN view.RelatedContract r
    ON e.ContractId = r.RelatedContractId AND r.RelationType = 2
```

---

## 事件/通知 Views

### view.Event

事件記錄。

| 欄位 | 類型 | 說明 |
|------|------|------|
| EventId | int | 事件 ID (PK) |
| EventType | nvarchar | 事件類型 |
| EventName | nvarchar | 事件名稱 |
| Description | nvarchar | 說明 |
| CreateDate | datetime | 建立日期 |
| CreateUserId | int | 建立者 ID |
| CreateUserName | nvarchar | 建立者名稱 |

---

### view.EventAttachment

事件附件。

| 欄位 | 類型 | 說明 |
|------|------|------|
| EventId | int | 事件 ID |
| AttachmentId | int | 附件 ID |
| FileName | nvarchar | 檔案名稱 |

---

### view.EventContract

事件關聯的合約。

| 欄位 | 類型 | 說明 |
|------|------|------|
| EventId | int | 事件 ID |
| ContractId | int | 合約 ID |
| ContractTitle | nvarchar | 合約標題 |

---

### view.AlertMailList

警示郵件清單。

| 欄位 | 類型 | 說明 |
|------|------|------|
| AlertId | int | 警示 ID |
| AlertType | nvarchar | 警示類型 |
| ContractId | int | 相關合約 ID |
| UserId | int | 收件人 ID |
| UserName | nvarchar | 收件人名稱 |
| Email | nvarchar | 電子郵件 |
| SendDate | datetime | 發送日期 |
| IsSent | bit | 是否已發送 |

---

## 其他 Views

### view.Project

專案資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ProjectId | int | 專案 ID (PK) |
| ProjectName | nvarchar | 專案名稱 |
| ProjectNo | nvarchar | 專案編號 |
| DepartmentId | int | 負責部門 ID |
| DepartmentName | nvarchar | 負責部門名稱 |
| StartDate | date | 開始日期 |
| EndDate | date | 結束日期 |
| IsActive | bit | 是否啟用 |

---

### view.SignRequirement

簽署需求。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| RequirementId | int | 需求 ID |
| RequirementType | nvarchar | 需求類型（用印/電子簽） |
| SignerName | nvarchar | 簽署人 |
| SignerTitle | nvarchar | 簽署人職稱 |
| SignDate | datetime | 簽署日期 |
| IsSigned | bit | 是否已簽署 |

---

### view.UrgentLevel

緊急程度定義。

| 欄位 | 類型 | 說明 |
|------|------|------|
| UrgentLevelId | int | 緊急程度 ID (PK) |
| UrgentLevelName | nvarchar | 名稱 |
| SlaMultiplier | decimal | SLA 乘數 (1=一般, 0.5=急件, 0=特急) |

---

### view.MainContractType

主合約類型。

| 欄位 | 類型 | 說明 |
|------|------|------|
| MainContractTypeId | int | 主類型 ID (PK) |
| MainContractTypeName | nvarchar | 主類型名稱 |
| ContractCategoryId | int | 合約分類 |
| IsActive | bit | 是否啟用 |

---

### view.SubContractType

子合約類型。

| 欄位 | 類型 | 說明 |
|------|------|------|
| SubContractTypeId | int | 子類型 ID (PK) |
| SubContractTypeName | nvarchar | 子類型名稱 |
| MainContractTypeId | int | 主類型 ID (FK) |
| IsActive | bit | 是否啟用 |

---

### view.Attachment

附件資訊。

| 欄位 | 類型 | 說明 |
|------|------|------|
| AttachmentId | int | 附件 ID (PK) |
| FileName | nvarchar | 檔案名稱 |
| FilePath | nvarchar | 檔案路徑 |
| FileSize | bigint | 檔案大小 |
| FileTypeId | int | 檔案類型 ID |
| UploadDate | datetime | 上傳日期 |
| UploadUserId | int | 上傳者 ID |

---

### view.LatestAttachment

最新附件（每個合約的最新版本）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| ContractId | int | 合約 ID |
| AttachmentId | int | 附件 ID |
| FileName | nvarchar | 檔案名稱 |
| FileTypeId | int | 檔案類型 ID |
| UploadDate | datetime | 上傳日期 |

---

### view.FileType

檔案類型定義。

| 欄位 | 類型 | 說明 |
|------|------|------|
| FileTypeId | int | 檔案類型 ID (PK) |
| FileTypeName | nvarchar | 檔案類型名稱 |
| Extension | nvarchar | 副檔名 |
| IsRequired | bit | 是否必要 |

---

### view.CombinedField

組合欄位（自定義顯示欄位）。

| 欄位 | 類型 | 說明 |
|------|------|------|
| FieldId | int | 欄位 ID (PK) |
| FieldName | nvarchar | 欄位名稱 |
| FieldExpression | nvarchar | 欄位運算式 |
| DisplayOrder | int | 顯示順序 |

---

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

---

## 注意事項

1. **所有查詢都有 1000 筆上限**：使用 `ORDER BY` 確保結果有意義
2. **日期函數**：使用 `GETDATE()`、`DATEADD()`、`DATEDIFF()` 進行日期運算
3. **NULL 處理**：`SaveNo IS NULL` 表示進行中，`SaveNo IS NOT NULL` 表示已結案
4. **效能考量**：先篩選再 JOIN，避免大量資料 JOIN
5. **分頁查詢**：如需分頁，使用 `OFFSET ... FETCH NEXT ...` 語法
