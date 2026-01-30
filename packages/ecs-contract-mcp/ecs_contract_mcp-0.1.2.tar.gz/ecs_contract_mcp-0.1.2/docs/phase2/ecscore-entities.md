# ECS Core Entity 模型詳細清單

> 本文件為 [ecscore-analysis.md](ecscore-analysis.md) 的補充資料

## 目錄結構

```
lib/Ltc.EcsDB/
├── EcsDbContext.cs                 # 主 DbContext（220+ DbSet）
├── Models/                         # 104 個 Entity 類別
├── PartialModels/                  # 部分類別擴展
├── CompiledModels/                 # EF Core 編譯模型
├── Repositories/                   # 資料庫存取層
├── ViewModels/                     # 127+ 個檢視模型
└── Extensions/                     # 擴展方法
```

---

## Entity 分類清單

### A. 合約主體（Contract Core）

| Entity | 說明 | 主要欄位 |
|--------|------|----------|
| **Contract** | 合約主表 | ContractId, DocumentName, RecorderId, CurrentStageId |
| ContractType | 合約類型 | ContractTypeId, ContractTypeName, MainContractTypeId |
| MainContractType | 主合約類型 | MainContractTypeId, Name |
| ContractType1 | 合約與類型對應 | （多對多關聯） |

#### Contract 欄位詳細

**基本資訊**：
- DocumentName, RecorderId, CreateDate, BranchId

**審查流程**：
- CurrentStageId, BackStageId, UrgentLevel

**價金**：
- Cost, CostNtd, FinalCost, FinalCostNtd, CostClause

**期效管理**：
- ValidStartDate, ValidEndDate, EffectiveDate
- AutoExtend, ExtendYear, ExtendMonth

**警示通知**：
- IsAlert, AlertBeginDate, AlertPeriod, AlertEmails

**保留欄位**（支援動態表單）：
```
Txt01-10, Memo01-15, Radio01-05, CheckBox01-05,
Select01-05, Int01-05, Double01-05, Date01-10
```

---

### B. 審查流程（Review/Exam Process）

| Entity | 說明 |
|--------|------|
| **ExamStage** | 審查關卡定義 |
| **ExamStatus** | 審查狀態（通過/退回/待審） |
| **ContractExaminer** | 合約指派審查人 |
| **ContractHistory** | 合約審查歷程 |
| ContractExamStageInfo | 關卡進度資訊 |
| ContractFlow | 審查流程定義 |
| ContractFlowStage | 流程關卡配置 |
| ExamResult | 審查結果 |
| CsexamResult | CS 審查結果 |

#### ContractHistory Type 欄位值

| 值 | 意義 |
|:--:|------|
| 0 | Exam（審查） |
| 1 | Sign（簽署） |
| 2 | AutoExtend（自動續約） |
| 3 | LTCExamChange（審查變更） |
| 4 | LTCSignChange（簽署變更） |
| 5 | LTCHide（隱藏） |

---

### C. 使用者與權限（User & Authority）

| Entity | 說明 |
|--------|------|
| **User** | 人員資料 |
| **Department** | 部門（樹狀結構） |
| UserDepartment | 使用者與部門對應 |
| Role | 角色定義 |
| UserRole | 使用者角色指派 |
| **Authority** | 權限定義 |
| AuthorityGroup | 權限群組 |
| UserAuthority | 使用者權限指派 |
| UserContractAuthority | 使用者合約權限 |
| UserContractAuthorityForDepartment | 部門級合約權限 |
| ExamStageAuthority | 關卡權限設定 |

#### User 主要欄位

- 基本：UserId, Name, LoginId, EmployeeId
- 聯絡：Email, Tel, Ext
- 部門：DepartmentId, BranchId, LineManager
- 職位：Title, PositionLevel
- 系統：Password, Role, Disable, Stop, LastLogin

---

### D. 相對人（Partner）

| Entity | 說明 |
|--------|------|
| **Partner** | 相對人主資料 |
| PartnerContact | 相對人聯絡人 |
| ContractPartner | 合約的相對人對應 |
| PartnerSignLog | 相對人簽署紀錄 |

---

### E. 附件（Attachment）

| Entity | 說明 |
|--------|------|
| **Attachment** | 附件檔案 |
| ContractAttachment | 合約附件對應 |
| ContractAttachmentChange | 附件變更歷程 |
| ContractAttachmentStatus | 附件審查狀態 |
| AttachmentGuid | 附件 GUID |
| AttachmentCertified | 認證附件 |
| AttachmentWatermark | 附件浮水印 |
| FileType | 檔案類型定義 |

---

### F. 簽署（Signature）

| Entity | 說明 |
|--------|------|
| SignRequirement | 簽署需求 |
| ContractRequireSign | 合約簽署要求 |
| ContractSignHistory | 合約簽署歷程 |
| SignAttachmentInfo | 簽署附件資訊 |
| EnvelopeInfo | 數位簽署信封 |
| EnvelopeStage | 信封關卡 |

---

### G. 事件與通知（Event & Notification）

| Entity | 說明 |
|--------|------|
| **Event** | 合約事件 |
| EventStatus | 事件狀態 |
| EventSendMailList | 事件郵件清單 |
| ContractEvent | 合約與事件對應 |
| MailLog | 郵件發送記錄 |
| ContractMailLog | 合約郵件記錄 |

---

### H. 代理（Acting）

| Entity | 說明 |
|--------|------|
| ActingEntry | 代行主紀錄 |
| ActingAgent | 代理人 |
| ActingContract | 代行的合約 |

---

## 完整 Entity 清單（104 個）

<details>
<summary>點擊展開</summary>

```
Acting, ActingAgent, ActingContract, ActingEntry, AgentJoinContract, ApiLog,
Attachment, AttachmentCertified, AttachmentGuid, AttachmentWatermark, Authority,
AuthorityChangeLog, AuthorityGroup, Classification, CloseStage, CloseStatus,
Contract, ContractAccessRelated, ContractAccessType, ContractAmount, ContractAttachment,
ContractAttachment1, ContractAttachmentChange, ContractAttachmentStatus, ContractClassification,
ContractCustomizedField, ContractCustomizedFieldForSearch, ContractEnvelopes, ContractEvent,
ContractExamStageInfo, ContractExaminer, ContractExaminer1, ContractExtendInfo, ContractFlow,
ContractFlowCsdefaultDepartment, ContractFlowCsdefaultExaminer, ContractFlowCsdefaultStage,
ContractFlowDefaultDepartment, ContractFlowDefaultExaminer, ContractFlowDefaultSyncStage,
ContractFlowStage, ContractGuid, ContractHistory, ContractMailLog, ContractNoCloseNotice,
ContractPartner, ContractRequireAttribute, ContractRequireSign, ContractSignHistory, ContractType,
ContractType1, ContractTypeLanguage, ContractViewTemp, CountryCode, CsexamResult, Department,
DepartmentTemp, Domain, EnvelopeAttachment, EnvelopeInfo, EnvelopeStage, Event, Event1,
EventSendMailExamStageList, EventSendMailList, EventStatus, ExamResult, ExamStage,
ExamStageAuthority, ExamStatus, ExamStatusLanguage, Exchange, FileType, LoginLog, MailLog,
MainContractDepartment, MainContractType, MainContractTypeLanguage, MessageLogs, Messages,
OtherContractAttachmentStatus, OtherExaminer, OtherExaminerAttachment, Otptoken, Partner,
PartnerContact, PartnerSignLog, RelatedContract, Role, SignAttachmentInfo, SignRequirement,
Snstore, StampDuty, TempAllCaseList, TempUpdateLog, UrgentLevel, User, UserAuthority,
UserContractAuthority, UserContractAuthorityForDepartment, UserDepartment, UserJoinRole, UserRole, Webconfig
```

</details>

---

## Schema 規則

| Schema | 用途 | 範例 |
|--------|------|------|
| dbo. | 主要表 | Contract, User |
| join. | 聯接表 | ActingAgent |
| data. | 資料表 | ActingEntry |
| view. | 檢視 | Acting |

---

## 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2026-01-21 | 從 EF Core 模型探索建立 |
