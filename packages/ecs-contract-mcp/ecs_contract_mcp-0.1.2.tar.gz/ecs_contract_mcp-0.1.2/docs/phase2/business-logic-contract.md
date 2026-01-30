# 合約業務邏輯分析

## 概述

本文件記錄 ECS 系統中合約（Contract）的核心業務邏輯，包括狀態管理、主要操作、實體關聯等。

---

## 一、合約生命週期

### 合約審核階段（ExamStageType）

合約在整個生命週期內會經過以下 **14 個審核階段**：

| ID | 代碼 | 階段名稱 | 說明 |
|----|------|---------|------|
| 1 | `Applicant` | 申請人 | 初始起案或申請人回覆 |
| 2 | `DirectorApproval` | 主管審核 | 部門主管核准 |
| 3 | `LegalAssignment` | 法務分案 | 分配給法務部門（會簽） |
| 4 | `LegalPreReview` | 法務初審 | ⚠️ 已不使用 |
| 5 | `LegalReview` | 法務審核 | 法務部門詳細審查 |
| 6 | `LegalDirectorReview` | 法務主管審核 | 法務部主管複審 |
| 7 | `FinalApproval` | 最終核准 | 公司高層最終核准 |
| 8 | `Signing` | 簽署用印 | 合約簽署（會簽） |
| 10 | `CoExamination` | 會辦審核 | 相關部門會簽意見 |
| 11 | `ContractArchive` | 結案歸檔 | 結案並歸檔（會簽） |
| 12 | `ApplicantContractArchive` | 申請人結案 | 申請人端結案歸檔（會簽） |
| 16 | `Withdrawn` | 撤案 | 撤銷合約 |
| 51 | `Docusign` | Docusign簽署 | 電子簽署（會簽） |
| 9 | `Legacy` | 舊資料 | 舊系統遺留資料 |

**會簽關卡**（parallelApprovalStageIds）：3, 8, 51, 11, 12
- 會簽關卡通過條件：任意一位審核人通過即可

### 審核結果（ExamResultType）

| ID | 代碼 | 結果名稱 | 說明 |
|----|------|---------|------|
| 1 | `Passed` | 通過 | 進入下一階段 |
| 2 | `Returned` | 退回 | 退回到指定階段重新修改 |
| 3 | `UnderReview` | 審核中 | 審核進行中（預設） |
| 4 | `RejectedClosed` | 退件結案 | 拒絕並終止合約 |

### 前端顯示狀態（ExamStageStatusCode）

| 代碼 | 狀態名稱 | 優先級 |
|------|---------|--------|
| `reject` | 退件結案 | 1 (最高) |
| `return` | 已退回 | 2 |
| `underCoReview` | 會辦審核中 | 3 |
| `accept` | 已通過 | 4 |
| `underReview` | 審核中 | 5 |
| `pending` | 等待中 | 6 |
| `unknown` | 未知 | 7 |

---

## 二、合約狀態流程圖

```
新增合約
  ↓
[申請人] ──起案──→ [主管審核] ──通過──→ [法務分案]
                   ↑                    ↓
                   └──退回──────────┐  [法務審核]
                                   ↓   ↓
                              [法務主管] ──通過→ [最終核准]
                                                  ↓
                                           [簽署用印/Docusign]
                                                  ↓
                              [會辦審核] ←────────┘
                                   ↓
                              [結案歸檔]
                                   ↓
                              ─────完成─────

終止操作: 任意階段 ──退件結案→ [終止]
撤案操作: 任意階段 ──撤案──→ [撤案]
```

**狀態轉換規則**：
1. **順序轉換**: 通過後進入下一階段
2. **退回轉換**: 可退回到申請人階段或指定的上游階段
3. **並行審核**: 某些階段（法務分案、簽署、結案）支持並行處理
4. **終止操作**: 任何階段都可選擇退件結案或撤案
5. **無序跳轉**: 已通過的階段可跳過（簽署不需要時自動過濾）

---

## 三、主要操作

### 1. 新增合約（createContractOfStandard）

**流程**：
```
驗證資料 → 建立合約主體 → 設置審核流程 → 分配審核人 → 建立會辦人 → 保存附件 → 完成
```

**關鍵操作**：
1. 建立 ApplyNo（申請號）
2. 根據合約類型和緊急程度自動獲取審核流程
3. 過濾簽署關卡（無簽署需求時）
4. 分配各階段審核人：
   - 申請人 → 起案階段
   - 直接審核人 → 主管審核階段
   - 默認法務人員 → 法務分案階段
5. 處理會辦簽署（coExaminers）

**驗證項目**：
- 部門ID存在
- 合約類型ID存在（若指定）
- 申請人、主管審核人存在
- 相對人（合約對方）存在
- 相關合約存在
- 幣別ID存在（若需要）
- 附件存在且檔案類型有效

### 2. 編輯合約（updateContractOfStandard）

**流程**：
```
驗證合約存在 → 驗證資料 → 建立歷程記錄 → 更新附件 → 更新合約資訊 → 完成
```

**限制條件**：
- 申請號和申請日期不可更新
- 自動建立 ContractHistory 記錄
- 只有特定審核階段可編輯

### 3. 審核合約（examineContractStage）

**核心操作**：
- **通過（Pass）**: 移至下一審核階段
- **退回（Return）**: 退回到指定階段
- **退件結案（RejectedClosed）**: 合約終止

**檢查項目**：
1. 驗證審核人權限
2. 驗證審核狀態ID有效性
3. 驗證退回階段（若為退回操作）
4. 更新審核人狀態和審核歷程

### 4. 結案歸檔（Archive）

**操作內容**：
1. 建立結案號（SaveNo）
2. 記錄結案日期、金額、幣別
3. 保存結案相關附件
4. 設置通知機制（事件追蹤）

**結案類型**：
- `ContractArchive`: 結案歸檔
- `ApplicantContractArchive`: 申請人端結案

### 5. 簽署操作（Signature）

**支持方式**：
- 傳統用印（Signing）
- Docusign 電子簽署

**簽署要求**：
- `requireSign`: 是否需要公司內部簽署
- `requirePartnerSign`: 是否需要交易對方簽署

---

## 四、合約關聯實體

### 1. 合約與附件

```
Contract
  └─ ContractAttachment (多對多)
       ├─ Attachment (檔案主體)
       │   ├─ FileType (檔案類型)
       │   └─ User (上傳者)
       └─ ExamStage (所屬關卡)
```

**按審核階段管理**：
- 起案階段：申請人上傳的原始附件
- 各審核階段：審核人可上傳意見附件
- 結案歸檔：歸檔時上傳最終文件

### 2. 合約與歷程

```typescript
ContractHistory {
  contractId: number,
  examStageId: number,      // 審核階段
  examStatusId: number,     // 審核狀態
  examUserId: number,       // 執行審核的人
  assignUserId?: number,    // 指派人
  examDate: Date,           // 審核日期
  examMemo: string,         // 審核意見
  type: number,             // 0=一般審核, 1=審核人異動
}
```

**歷程記錄時機**：
- 合約新增：初始化流程
- 合約編輯：「基本資料更新」
- 審核操作：「通過/退回/結案」
- 法務資訊更新：「法務內部資訊更新」

### 3. 合約與審核人

```typescript
// 主審核人
ContractExaminer {
  contractId, examStageId, userId,
  examStatusId,    // 審核狀態
  examSeq,         // 序列號（並行審核）
  examStageSeq,    // 階段序列
  stayDate,        // 滯留日期
  assignDate,      // 指派日期
  examDate         // 審核完成日期
}

// 會辦人
OtherExaminer {
  contractId, examinerSn, userId,
  halt: boolean,        // 必要回覆
  replied: boolean,     // 是否已回覆
  deadline?: number,    // 截止天數
  alertPeriod?: number, // 提醒間隔
}
```

### 4. 合約與相關合約

```typescript
RelatedContract {
  contractId,              // 主合約
  relatedContractId,       // 被關聯的合約
  contractRequireAttributeSn,
}
```

**關聯類型**：
- `create`: 新增合約
- `renew`: 續約
- `update`: 更新
- `terminate`: 終止
- `other`: 其他

### 5. 合約金額資訊

```typescript
ContractAmount {
  contractId,
  cost?: number,           // 合約金額
  exchangeTypeId?: number, // 幣別
  tax: number,             // 是否含稅
  payPeriod?: string       // 付款條件
}
```

### 6. 合約調閱（特殊模組）

```typescript
Contract {
  contractModuleSn: number,  // 1=一般合約, 2=合約調閱

  // 調閱專用欄位
  accessingMethod?: string,  // 線上/正本/影本
  accessStartDate?: Date,
  accessEndDate?: Date,
  accessingReason?: string
}
```

---

## 五、關鍵檔案位置

### ecs-ten-main（前台）

| 類型 | 檔案路徑 |
|------|---------|
| 合約服務 | `packages/ecs-ten-server/src/services/contract-service.ts` |
| 審核階段服務 | `packages/ecs-ten-server/src/services/contract-exam-stage-service.ts` |
| 結案服務 | `packages/ecs-ten-server/src/services/archive-service.ts` |
| 簽署服務 | `packages/ecs-ten-server/src/services/contract-signature-service.ts` |
| 會辦服務 | `packages/ecs-ten-server/src/services/co-examiner-service.ts` |
| 合約 Repository | `packages/ecs-ten-server/src/repositories/contract-repository.ts` |
| 審核人 Repository | `packages/ecs-ten-server/src/repositories/contract-examiner-repository.ts` |
| 歷程 Repository | `packages/ecs-ten-server/src/repositories/contract-history-repository.ts` |
| 附件 Repository | `packages/ecs-ten-server/src/repositories/contract-attachment-repository.ts` |

### ecscore-master（後台）

| 類型 | 檔案路徑 |
|------|---------|
| 合約 Controller | `packages/webapp.apicore/Controllers/ContractController.cs` |
| 合約 Repository | `lib/Ltc.EcsDB/Repositories/ContractRepository.cs` |
| 審核人 Repository | `lib/Ltc.EcsDB/Repositories/ContractExaminerRepository.cs` |
| 歷程 Repository | `lib/Ltc.EcsDB/Repositories/ContractHistoryRepository.cs` |
| 階段類型 Enum | `lib/Ltc.EcsDB/Enum/ExamStageType.cs` |
| 狀態類型 Enum | `lib/Ltc.EcsDB/Enum/ExamStatusType.cs` |
