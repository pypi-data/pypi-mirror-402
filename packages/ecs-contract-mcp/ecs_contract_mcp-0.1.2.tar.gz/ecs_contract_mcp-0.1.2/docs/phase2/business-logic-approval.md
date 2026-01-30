# 審核流程邏輯分析

## 概述

本文件記錄 ECS 系統中審核/簽核流程（Approval Flow）的核心邏輯，包括關卡設定、狀態機、會辦機制等。

---

## 一、審核關卡類型

### ExamStage 關卡定義

| ID | 代碼 | 關卡名稱 | 是否會簽 | 說明 |
|----|------|---------|---------|------|
| 1 | Applicant | 申請人 | ✗ | 申請人提交或回覆 |
| 2 | DirectorApproval | 主管審核 | ✗ | 部門主管核准 |
| 3 | LegalAssignment | 法務分案 | ✓ | 法務部分配案件 |
| 4 | LegalPreReview | 法務初審 | ✗ | ⚠️ 已不使用 |
| 5 | LegalReview | 法務實審 | ✗ | 法務進行實質審核 |
| 6 | LegalDirectorReview | 法務主管審查 | ✗ | 法務主管複審 |
| 7 | FinalApproval | 最終核准人 | ✗ | 最終核准人審查 |
| 8 | Signing | 簽署用印 | ✓ | 簽署與用印 |
| 10 | CoExamination | 會辦簽署意見 | ✗ | 會辦單位回覆 |
| 11 | ContractArchive | 結案歸檔 | ✓ | 合約完成結案 |
| 12 | ApplicantContractArchive | 申請人結案 | ✓ | 申請人端結案 |
| 16 | Withdrawn | 撤案 | ✗ | 案件撤銷 |
| 51 | Docusign | Docusign簽署 | ✓ | 電子簽署 |

**會簽關卡** (parallelApprovalStageIds): `[3, 8, 51, 11, 12]`
- 會簽關卡只需任一審核人通過即可
- 非會簽關卡需全部審核人通過

---

## 二、審核狀態

### 審核結果（ExamResultType）

| ID | 代碼 | 名稱 | 權限代碼 |
|----|------|------|---------|
| 1 | Passed | 通過 | `auditApprove` |
| 2 | Returned | 退回 | `auditReject` |
| 3 | UnderReview | 審核中 | `auditUnderReview` |
| 4 | RejectedClosed | 退件結案 | `auditCloseOnReject` |

### 前端階段狀態（ExamStageStatusType）

| 代碼 | 中文描述 | 優先級 | 說明 |
|------|---------|--------|------|
| RejectedClosed | 退件結案 | 1 | 最高優先級 |
| Returned | 已退回 | 2 | |
| UnderCoExaminerReview | 會辦回覆中 | 3 | 等待會辦 |
| Passed | 已通過 | 4 | |
| UnderReview | 審核中 | 5 | |
| Unassigned | 尚未指派 | 6 | |
| Unknown | 預期外狀態 | 7 | 異常狀態 |

### 後端詳細狀態（部分）

| ID | 狀態名稱 | 所屬階段 | 結果 |
|----|---------|---------|------|
| 1 | 起案 | New | - |
| 3 | 主管審核通過 | DirectorApproval | Passed |
| 4 | 主管退回 | DirectorApproval | Returned |
| 6 | 主管審核不核准 | DirectorApproval | Rejected |
| 7 | 法務分案核准 | LegalAssignment | Passed |
| 12 | 申請人回覆中 | Applicant | - |
| 15 | 法務審核核准 | LegalReview | Passed |
| 18 | 法務審核中 | LegalReview | Examining |
| 20 | 法務主管審核通過 | LegalDirectorReview | Passed |
| 23 | 同意簽署 | Signing | Passed |
| 26 | 撤案 | CaseWithdrawn | - |
| 30 | 已簽署 | Signing | Signed |

---

## 三、流程配置

### 資料結構

```
ContractFlow (合約流程)
  ├─ ContractTypeId (合約類型)
  ├─ UrgentLevelId (緊急程度)
  └─ ContractFlowStage[] (流程階段列表)
       ├─ ExamStageId (審核關卡)
       ├─ Deadline (截止天數)
       └─ ContractFlowDefaultExaminer[] (預設審核人)
            ├─ UserId (審核人ID)
            ├─ Cc (副本人員)
            └─ ContractFlowDefaultDepartment[] (適用部門)
```

### 流程配置邏輯

1. **依合約類型和緊急程度**決定使用哪個流程
2. **各關卡可配置**：
   - 截止天數（Deadline）
   - 預設審核人
   - 適用部門範圍
3. **動態過濾**：無簽署需求時自動跳過簽署關卡

---

## 四、審核人與記錄

### ContractExaminer（主審核人）

| 欄位 | 說明 |
|------|------|
| ContractId | 合約ID |
| ExamStageId | 審核關卡ID |
| ExamStatusId | 審核狀態ID |
| UserId | 審核人ID |
| ExamMemo | 審核意見 |
| ExamDate | 審核日期 |
| AssignDate | 指派日期 |
| ExamSeq | 審核人順序（同一關卡可多人） |
| ExamStageSeq | 關卡順序 |
| SignType | 簽署類別 |
| Signer | 簽署人 |
| ReAssign | 是否重新指派 |

### OtherExaminer（會辦人）

| 欄位 | 說明 |
|------|------|
| ExaminerSn | 主審核人序列號 |
| UserId | 會辦人ID |
| RequireMemo | 需求意見 |
| ReplyMemo | 回應訊息 |
| Replied | 是否已回應 |
| **Halt** | **是否必要回覆（關鍵）** |
| CsexamResultId | 會辦審核結果ID |
| Deadline | 截止天數 |
| AlertPeriod | 提醒期間 |
| GroupId | 邀約會辦群組編號 |

---

## 五、會辦機制

### 會辦流程

```
在任何審核關卡，審核人可邀約會辦單位
  ├─ Halt=true 時，流程需等待所有必要會辦回覆
  └─ Halt=false 時，流程不受會辦回覆影響

會辦回覆狀態：
  ├─ Replied=false → 未回覆（若Halt=true則阻止流程）
  └─ Replied=true → 已回覆（CsexamResultId 記錄結果）
```

### 會辦特性

- 同一審核人可有多個會辦（不同群組或部門）
- `Halt=true`：必要回覆，流程需等待
- `Halt=false`：參考意見，不阻止流程
- 可設定截止日期和提醒間隔
- 支持自動發送提醒信件
- 可指定抄送人員（carbonNotify）

---

## 六、審核動作

| 動作 | 審核結果 | 權限 | 說明 |
|------|---------|------|------|
| 送審 | - | - | 起案時分配審核人 |
| 核准 | Passed (1) | `auditApprove` | 流程進行到下一關 |
| 退回 | Returned (2) | `auditReject` | 回到申請人修正 |
| 退件結案 | RejectedClosed (4) | `auditCloseOnReject` | 案件終止 |
| 加簽/分案 | - | - | 審核人異動 |
| 會簽 | - | - | 邀約會辦單位 |

### 審核人異動類型

- `Add` (1)：新增審核人
- `Remove` (2)：移除審核人

---

## 七、簽署要求

### SignRequirement（簽署類型）

| 欄位 | 說明 |
|------|------|
| SignTypeId | 簽署類型ID |
| Name | 簽署類型名稱 |
| SignType | 簽署類型（字元） |
| CustodianUserId | 印章保管人ID |
| SealCode | 印章代碼 |
| BelongOwner | 所屬單位 |
| Purpose | 用途 |
| Enabled | 是否啟用 |

### ContractSignHistory（簽署記錄）

- 記錄合約簽署的歷程
- 關聯審核階段和審核人
- 記錄簽署人和簽署日期

---

## 八、流程狀態機

### 標準流程

```
申請人提交
  → 主管審核 [通過|退回]
  → 法務分案 [任一通過|全拒]
  → 法務審核 [通過|退回]
  → 法務主管 [通過|退回]
  → 最終核准 [通過|退回]
  → 簽署用印 [任一通過|全拒]
  → 邀約會辦 [等待回覆]
  → 結案歸檔 [完成]
```

### 狀態計算邏輯

```typescript
// 優先級邏輯（由高到低）
calculateExamStageStatus() {
  RejectedClosed > Returned > UnderCoExaminerReview >
  Passed > UnderReview > Unassigned
}

// 會簽判斷
isStagePassed(stage) {
  if (isParallelStage) {
    return anyExaminerPassed; // 任一通過
  } else {
    return allExaminersPassed; // 全部通過
  }
}
```

### 可執行操作

在任何階段均可：
- 退回到前面的關卡
- 邀約會辦進行協簽
- 轉移審核人
- 記錄審核意見和附件

---

## 九、相關資料表

| 功能 | 主要表 | 關鍵欄位 |
|------|--------|--------|
| 流程定義 | `ContractFlow` | ContractTypeId, UrgentLevelId |
| 流程階段 | `ContractFlowStage` | ExamStageId, Deadline |
| 預設審核人 | `ContractFlowDefaultExaminer` | UserId, Cc |
| 審核階段 | `ExamStage` | ExamStageId, Name, SystemDefine |
| 審核結果 | `ExamResult` | ExamResultId, Name |
| 審核狀態 | `ExamStatus` | ExamStatusId, ExamStageId, ExamResultId |
| 合約審核人 | `ContractExaminer` | ContractId, ExamStageId, ExamStatusId |
| 會辦審核 | `OtherExaminer` | ExaminerSn, UserId, Halt |
| 簽署要求 | `SignRequirement` | SignTypeId, Name |
| 簽署記錄 | `ContractSignHistory` | ContractId, ExamStageId |

---

## 十、關鍵檔案位置

### ecscore-master（後台）

| 類型 | 檔案路徑 |
|------|---------|
| ExamStageType Enum | `lib/Ltc.EcsDB/Enum/ExamStageType.cs` |
| ExamResultType Enum | `lib/Ltc.EcsDB/Enum/ExamResultType.cs` |
| ExamStatusType Enum | `lib/Ltc.EcsDB/Enum/ExamStatusType.cs` |
| ContractFlow Model | `lib/Ltc.EcsDB/Models/ContractFlow.cs` |
| ContractFlowStage Model | `lib/Ltc.EcsDB/Models/ContractFlowStage.cs` |
| ContractExaminer Model | `lib/Ltc.EcsDB/Models/ContractExaminer.cs` |
| OtherExaminer Model | `lib/Ltc.EcsDB/Models/OtherExaminer.cs` |
| SignRequirement Model | `lib/Ltc.EcsDB/Models/SignRequirement.cs` |
| FlowStage 業務邏輯 | `lib/Ltc.EcsCode/Core/Lib/Contract/FlowStage.cs` |
| ExamStage Controller | `packages/webapp.apicore/Controllers/ExamStageController.cs` |
| ExamStatus Controller | `packages/webapp.apicore/Controllers/ExamStatusController.cs` |

### ecs-ten-main（前台）

| 類型 | 檔案路徑 |
|------|---------|
| exam-stage-schema | `packages/ecs-ten-server/src/schema/exam-stage-schema.ts` |
| exam-result-schema | `packages/ecs-ten-server/src/schema/exam-result-schema.ts` |
| exam-status-schema | `packages/ecs-ten-server/src/schema/exam-status-schema.ts` |
| exam-stage-status-schema | `packages/ecs-ten-server/src/schema/exam-stage-status-schema.ts` |
| co-examiner-schema | `packages/ecs-ten-server/src/schema/co-examiner-schema.ts` |
| ExamStageStatusService | `packages/ecs-ten-server/src/services/exam-stage-status-service.ts` |
| ExamStatusService | `packages/ecs-ten-server/src/services/exam-status-service.ts` |
| ContractExamStageService | `packages/ecs-ten-server/src/services/contract-exam-stage-service.ts` |
| CoExaminerService | `packages/ecs-ten-server/src/services/co-examiner-service.ts` |
