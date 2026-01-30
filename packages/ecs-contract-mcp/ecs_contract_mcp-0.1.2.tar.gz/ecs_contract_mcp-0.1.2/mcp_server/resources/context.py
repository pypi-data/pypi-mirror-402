"""Context Resources - 業務脈絡知識

提供 AI 所需的業務背景知識：
- ecs://context/business-terms - 業務術語定義
- ecs://context/contract-lifecycle - 合約生命週期
- ecs://context/approval-flow - 審核流程說明
- ecs://context/sla-definitions - SLA 定義
"""

from mcp.server.fastmcp import FastMCP


def register_context_resources(mcp: FastMCP) -> None:
    """註冊 Context 相關 Resources"""

    @mcp.resource("ecs://context/business-terms")
    def get_business_terms() -> str:
        """業務術語定義"""
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

## 審核動作

| 動作 | ExamStatusId | 說明 |
|------|-------------:|------|
| 通過 | 1 | 審核人核准，進入下一階段 |
| 退回 | 2 | 退回修改（通常退回申請人階段） |
| 審核中 | 3 | 等待審核人處理 |
| 退件結案 | 4 | 拒絕並終止整個案件 |

## 合約金額相關

| 術語 | 說明 |
|------|------|
| **Cost** | 合約金額（以 ExchangeTypeId 指定的幣別計算） |
| **ExchangeTypeId** | 幣別 ID |
| **ExchangeName** | 幣別名稱（如：TWD、USD、CNY） |

## 時間相關欄位

| 欄位 | 說明 |
|------|------|
| **CreateDate** | 合約建立日期（送出申請的時間） |
| **ValidStartDate** | 合約生效日 |
| **ValidEndDate** | 合約到期日 |
| **AutoExtend** | 是否自動展延（bit，1=是） |
| **StayDate** | 進入某審核階段的時間 |
| **ExamDate** | 完成審核的時間 |
"""

    @mcp.resource("ecs://context/contract-lifecycle")
    def get_contract_lifecycle() -> str:
        """合約生命週期"""
        return """# 合約生命週期

## 標準流程

```
新增合約
    |
+---------------+
|  申請人起案   | ExamStageId = 1
+---------------+
    |
+---------------+
|  主管審核     | ExamStageId = 2
+---------------+
    |
+---------------+
|  法務分案     | ExamStageId = 3 (會簽)
+---------------+
    |
+---------------+
|  法務審核     | ExamStageId = 5
+---------------+
    |
+---------------+
| 法務主管審核  | ExamStageId = 6
+---------------+
    |
+---------------+
|  最終核准     | ExamStageId = 7
+---------------+
    |
+---------------+
|  簽署用印     | ExamStageId = 8 或 51 (DocuSign)
+---------------+
    |
+---------------+
|  結案歸檔     | ExamStageId = 11
+---------------+
    |
  完成（SaveNo 有值）
```

## 會簽關卡

會簽 = 多人可同時審核，任一人通過即可。

**會簽階段 ID**：3, 8, 11, 12, 51

## 狀態轉換

### 正常流程
- 申請人提交 → 主管審核 → 法務分案 → ... → 結案歸檔 → 完成

### 退回流程
- 任何階段 → (退回) → 申請人修改 → 重新提交 → 繼續流程

### 撤案
- 任何階段 → (撤案, ExamStageId = 16) → 案件終止

### 退件結案
- 任何階段 → (退件結案, ExamStatusId = 4) → 案件終止

## 重要觀察點

### 判斷合約是否在審核中
```sql
SELECT * FROM view.Contract
WHERE SaveNo IS NULL AND CurrentStageId IS NOT NULL
```

### 判斷合約是否已完成
```sql
SELECT * FROM view.Contract
WHERE SaveNo IS NOT NULL
```

### 查看合約目前卡在哪個階段
```sql
SELECT c.ContractId, c.Title, c.CurrentStageName,
       e.UserName as CurrentExaminer, e.StayDate
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL AND e.ExamStatusId = 3
```
"""

    @mcp.resource("ecs://context/approval-flow")
    def get_approval_flow() -> str:
        """審核流程說明"""
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
| 51 | Docusign | DocuSign 電子簽章 |

## 審核狀態

| ExamStatusId | 名稱 | 說明 |
|-------------:|------|------|
| 1 | 通過 | 審核通過，進入下一階段 |
| 2 | 退回 | 退回申請人修改 |
| 3 | 審核中 | 等待審核 |
| 4 | 退件結案 | 拒絕並終止 |

## 退回機制

- 任何階段都可以退回到「申請人」階段
- 退回時需填寫原因（ExamMemo）
- 退回紀錄保存在 ContractHistory

### 查詢退回紀錄
```sql
SELECT c.ContractId, c.Title, h.ExamStageName, h.ExamUserName, h.ExamMemo, h.ExamDate
FROM view.ContractHistory h
JOIN view.Contract c ON h.ContractId = c.ContractId
WHERE h.ExamStatusId = 2  -- 退回
ORDER BY h.ExamDate DESC
```

## 會辦機制

會辦是跨部門徵詢意見的機制。

| Halt | Replied | 狀態 |
|:----:|:-------:|------|
| 0 | - | 非必要會辦（FYI，僅供參考） |
| 1 | 0 | 必要會辦，尚未回覆（阻塞中） |
| 1 | 1 | 必要會辦，已回覆 |

### 會辦阻塞查詢
```sql
SELECT c.ContractId, c.Title, o.UserName, o.DepartmentName,
       o.Deadline, DATEDIFF(day, o.CreateDate, GETDATE()) as WaitingDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
ORDER BY WaitingDays DESC
```

### 會辦逾期查詢
```sql
SELECT c.ContractId, c.Title, o.UserName, o.Deadline,
       DATEDIFF(day, o.CreateDate, GETDATE()) as ActualDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
  AND DATEDIFF(day, o.CreateDate, GETDATE()) > o.Deadline
ORDER BY ActualDays DESC
```

## 代理機制

- 審核人可設定代理人
- 代理期間內，代理人可代為審核
- 代理設定見 view.Acting 系列 View
"""

    @mcp.resource("ecs://context/sla-definitions")
    def get_sla_definitions() -> str:
        """SLA 定義"""
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
| 2 | 急件 | 標準天數 * 0.5 |
| 3 | 特急 | 1 天 |

## SLA 計算方式

- **滯留時間** = `DATEDIFF(day, StayDate, GETDATE())` 或 `DATEDIFF(day, StayDate, ExamDate)`
- **逾期判斷** = 滯留時間 > 標準天數（考慮緊急程度調整）

## 逾期查詢範例

### 法務審核逾期案件（標準 5 天）
```sql
SELECT c.ContractId, c.Title, c.RecorderName,
       e.UserName as Examiner, e.StayDate,
       DATEDIFF(day, e.StayDate, GETDATE()) as DaysInStage
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL
  AND e.ExamStageId = 5
  AND e.ExamStatusId = 3
  AND DATEDIFF(day, e.StayDate, GETDATE()) > 5
ORDER BY DaysInStage DESC
```

### 各階段逾期案件統計
```sql
SELECT e.ExamStageName,
       COUNT(*) as OverdueCount,
       AVG(DATEDIFF(day, e.StayDate, GETDATE())) as AvgOverdueDays
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL
  AND e.ExamStatusId = 3
  AND DATEDIFF(day, e.StayDate, GETDATE()) >
      CASE e.ExamStageId
          WHEN 2 THEN 3   -- 主管審核
          WHEN 3 THEN 1   -- 法務分案
          WHEN 5 THEN 5   -- 法務審核
          WHEN 6 THEN 3   -- 法務主管審核
          WHEN 7 THEN 5   -- 最終核准
          WHEN 8 THEN 3   -- 簽署用印
          WHEN 11 THEN 3  -- 結案歸檔
          ELSE 7          -- 其他預設 7 天
      END
GROUP BY e.ExamStageId, e.ExamStageName
ORDER BY OverdueCount DESC
```

### 審核效率統計（各階段平均處理天數）
```sql
SELECT e.ExamStageName,
       COUNT(*) as CaseCount,
       AVG(DATEDIFF(day, e.StayDate, e.ExamDate)) as AvgDays,
       MIN(DATEDIFF(day, e.StayDate, e.ExamDate)) as MinDays,
       MAX(DATEDIFF(day, e.StayDate, e.ExamDate)) as MaxDays
FROM view.ContractExaminer e
WHERE e.ExamDate IS NOT NULL
  AND e.ExamDate >= DATEADD(month, -3, GETDATE())
GROUP BY e.ExamStageId, e.ExamStageName
ORDER BY e.ExamStageId
```

## 會辦 SLA

| 會辦類型 | 標準天數 |
|---------|--------:|
| 一般會辦 | 7 天 |
| 緊急會辦 | 3 天 |

### 會辦逾期查詢
```sql
SELECT c.ContractId, c.Title, o.UserName, o.DepartmentName,
       o.Deadline,
       DATEDIFF(day, o.CreateDate, GETDATE()) as ActualDays,
       DATEDIFF(day, o.CreateDate, GETDATE()) - o.Deadline as OverdueDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
  AND DATEDIFF(day, o.CreateDate, GETDATE()) > o.Deadline
ORDER BY OverdueDays DESC
```
"""
