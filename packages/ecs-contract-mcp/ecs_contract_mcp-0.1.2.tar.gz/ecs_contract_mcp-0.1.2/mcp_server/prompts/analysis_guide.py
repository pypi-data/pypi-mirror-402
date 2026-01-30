"""Analysis guide prompts for ECS MCP Server"""

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all prompts with the MCP server

    Args:
        mcp: The FastMCP server instance
    """

    @mcp.prompt()
    def data_analysis_guide() -> str:
        """資料分析框架指引

        提供 ECS 合約資料分析的步驟框架，幫助 AI 有系統地回答用戶問題。
        """
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

使用 `query_database` Tool 執行 SQL 查詢：
- 每次查詢都明確說明 purpose
- 使用 ORDER BY 確保結果有意義
- 如結果被截斷，加入篩選條件
- 只能查詢 view.* 開頭的 View

### ⚠️ 查詢效能注意事項

**絕對避免**：
- 多個 `LIKE '%name%'` 的 OR 條件（會超時）
- 一次返回大量明細資料（會造成 context 爆炸）
- 在文字欄位上做模糊搜尋

**最佳實踐**：
1. **人員查詢必須用 ID**：先從 `view.User` 用名字查 `UserID`，再用 ID 查其他表
2. **優先返回統計**：使用 `COUNT(*)`、`GROUP BY` 返回彙總數據
3. **分步查詢**：複雜問題拆成多個簡單查詢
4. **限制欄位**：只選必要欄位，避免 SELECT *

## Step 5: 匯總回答

- 整合多個查詢結果
- 提供分析洞察
- 標註資料時間點

---

## 重要判斷邏輯速查

### 合約狀態
| 狀態 | SQL 條件 |
|------|---------|
| 進行中 | `SaveNo IS NULL` |
| 已結案 | `SaveNo IS NOT NULL` |
| 審核中 | `SaveNo IS NULL AND CurrentStageId IS NOT NULL` |
| 已到期 | `ValidEndDate < GETDATE()` |
| 即將到期 | `ValidEndDate BETWEEN GETDATE() AND DATEADD(day, N, GETDATE())` |

### 合約分類
| 分類 | SQL 條件 |
|------|---------|
| 銷售（客戶合約） | `ContractCategoryId = 1` |
| 採購（供應商合約） | `ContractCategoryId = 2` |
| 其他 | `ContractCategoryId = 3` |

### 審核狀態
| 狀態 | ExamStatusId |
|------|-------------|
| 通過 | 1 |
| 退回 | 2 |
| 審核中 | 3 |
| 退件結案 | 4 |

### 會辦判斷
| 狀態 | SQL 條件 |
|------|---------|
| 會辦阻塞中 | `Halt = 1 AND Replied = 0` |
| 會辦完成 | `Replied = 1` |
| 非必要會辦（FYI） | `Halt = 0` |
"""

    @mcp.prompt()
    def common_queries() -> str:
        """常見查詢範例

        提供各種常見分析場景的 SQL 範例，可作為撰寫查詢的參考。
        """
        return """# 常見查詢範例

以下是各種常見分析場景的 SQL 範例，可作為撰寫查詢的參考。

---

## 合約到期預警

```sql
-- 90 天內到期的進行中合約
SELECT ContractId, Title, PartnerName, ValidEndDate,
       DATEDIFF(day, GETDATE(), ValidEndDate) as DaysUntilExpiry
FROM view.Contract
WHERE SaveNo IS NULL
  AND ValidEndDate BETWEEN GETDATE() AND DATEADD(day, 90, GETDATE())
ORDER BY ValidEndDate
```

---

## 各部門合約金額統計

```sql
-- 按部門統計進行中合約數量與金額
SELECT DepartmentName,
       COUNT(*) as ContractCount,
       SUM(Cost) as TotalAmount
FROM view.Contract
WHERE SaveNo IS NULL
GROUP BY DepartmentId, DepartmentName
ORDER BY TotalAmount DESC
```

---

## 審核效率統計

```sql
-- 近一個月各審核階段平均處理天數
SELECT ExamStageName,
       COUNT(*) as CaseCount,
       AVG(DATEDIFF(day, StayDate, ExamDate)) as AvgDays
FROM view.ContractExaminer
WHERE ExamDate IS NOT NULL
  AND ExamDate >= DATEADD(month, -1, GETDATE())
GROUP BY ExamStageId, ExamStageName
ORDER BY ExamStageId
```

---

## 會辦阻塞案件

```sql
-- 目前會辦阻塞中的案件（按等待天數排序）
SELECT c.ContractId, c.Title, o.UserName, o.DepartmentName,
       DATEDIFF(day, o.CreateDate, GETDATE()) as WaitingDays
FROM view.Contract c
JOIN view.OtherExaminer o ON c.ContractId = o.ContractId
WHERE o.Halt = 1 AND o.Replied = 0
ORDER BY WaitingDays DESC
```

---

## 退回率統計

```sql
-- 近三個月各部門退回率
SELECT DepartmentName,
       COUNT(DISTINCT ContractId) as TotalCases,
       SUM(CASE WHEN ExamStatusId = 2 THEN 1 ELSE 0 END) as ReturnCount
FROM view.ContractHistory h
JOIN view.Contract c ON h.ContractId = c.ContractId
WHERE h.ExamDate >= DATEADD(month, -3, GETDATE())
GROUP BY c.DepartmentId, c.DepartmentName
```

---

## 合約類型分布

```sql
-- 進行中合約的類型分布
SELECT ContractTypeName, ContractCategoryId,
       COUNT(*) as ContractCount,
       SUM(Cost) as TotalAmount
FROM view.Contract
WHERE SaveNo IS NULL
GROUP BY ContractTypeId, ContractTypeName, ContractCategoryId
ORDER BY ContractCount DESC
```

---

## 特定相對人合約

```sql
-- 查詢特定相對人的所有合約
SELECT ContractId, Title, ContractTypeName, ValidStartDate, ValidEndDate,
       Cost, ExchangeCode, SaveNo
FROM view.Contract
WHERE PartnerName LIKE '%台積電%'
ORDER BY CreateDate DESC
```

---

## 審核中案件清單

```sql
-- 目前在審核中的案件（依審核階段分類）
SELECT c.ContractId, c.Title, c.PartnerName,
       e.ExamStageName, e.UserName as CurrentExaminer,
       DATEDIFF(day, e.StayDate, GETDATE()) as DaysInStage
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL
  AND c.CurrentStageId IS NOT NULL
  AND e.ExamStatusId = 3
ORDER BY e.ExamStageId, DaysInStage DESC
```

---

## 逾期案件（以法務審核為例）

```sql
-- 法務審核階段逾期案件（超過 5 天）
SELECT c.ContractId, c.Title,
       DATEDIFF(day, e.StayDate, GETDATE()) as DaysInStage
FROM view.Contract c
JOIN view.ContractExaminer e ON c.ContractId = e.ContractId
WHERE c.SaveNo IS NULL
  AND e.ExamStageId = 5
  AND e.ExamStatusId = 3
  AND DATEDIFF(day, e.StayDate, GETDATE()) > 5
ORDER BY DaysInStage DESC
```

---

## 月度新增合約趨勢

```sql
-- 近 12 個月每月新增合約數量
SELECT FORMAT(CreateDate, 'yyyy-MM') as YearMonth,
       COUNT(*) as NewContracts,
       SUM(Cost) as TotalAmount
FROM view.Contract
WHERE CreateDate >= DATEADD(month, -12, GETDATE())
GROUP BY FORMAT(CreateDate, 'yyyy-MM')
ORDER BY YearMonth
```

---

## 關聯合約查詢

```sql
-- 查詢某合約的所有關聯合約
SELECT rc.RelatedContractId, c.Title, rc.RelationType,
       CASE rc.RelationType
           WHEN 1 THEN '新增'
           WHEN 2 THEN '續約'
           WHEN 3 THEN '變更'
           WHEN 4 THEN '終止'
       END as RelationTypeName
FROM view.RelatedContract rc
JOIN view.Contract c ON rc.RelatedContractId = c.ContractId
WHERE rc.ContractId = 12345
```

---

## 人員在合約中的角色查詢（重要！）

**⚠️ 效能警告**：查詢人員相關資料時，**絕對不要**直接用名字做 LIKE 搜尋！
這會導致查詢超時或返回過多資料。

**正確做法**：先查 UserID，再用 ID 查詢。

```sql
-- Step 1: 先從 User 表查詢 UserID（只需一次）
SELECT UserID, UserName, UserDepartment, Title
FROM view.User
WHERE UserName LIKE '%張瑩珠%'
-- 結果: UserID = 102
```

```sql
-- Step 2: 用 UserID 查詢角色統計（高效！）
-- 2a. 作為合約承辦人
SELECT '合約承辦人' AS 角色, COUNT(*) AS 數量
FROM view.Contract WHERE RecorderID = 102

-- 2b. 作為當前審查者
SELECT '當前審查者' AS 角色, COUNT(*) AS 數量
FROM view.Contract WHERE CurrentExaminerID = 102

-- 2c. 在審查紀錄中的角色分佈
SELECT ExamStage AS 審查階段, COUNT(*) AS 數量
FROM view.ContractExaminer
WHERE UserID = 102
GROUP BY ExamStage
ORDER BY COUNT(*) DESC

-- 2d. 審查結果統計
SELECT ExamResult AS 結果, COUNT(*) AS 數量
FROM view.ContractExaminer
WHERE UserID = 102
GROUP BY ExamResult
```

```sql
-- Step 3: 如需明細，只取少量範例（加 TOP 限制）
SELECT TOP 5 ContractID, DocumentName, ExamStage, ExamStatus, AssignDate
FROM view.ContractExaminer ce
JOIN view.Contract c ON ce.ContractID = c.ContractID
WHERE ce.UserID = 102 AND ce.ExamStatus = '審核中'
ORDER BY ce.AssignDate DESC
```

**錯誤範例（會超時！）**：
```sql
-- ❌ 千萬不要這樣做！
SELECT * FROM view.Contract
WHERE RecorderName LIKE '%張瑩珠%'
   OR Examiners LIKE '%張瑩珠%'
   OR ApplicantNames LIKE '%張瑩珠%'
   OR CurrentExaminer LIKE '%張瑩珠%'
-- 這會導致全表掃描，多個 OR 條件更糟糕
```
"""
