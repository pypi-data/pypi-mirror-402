# ECS 資料庫 Schema 文件

> 本文件為資料庫結構的單一資訊來源，前後端分析文件應引用此處。

## 資料庫資訊

| 項目 | 值 |
|------|-----|
| 資料庫伺服器 | ecs2022.ltc |
| 資料庫名稱 | LT_ECS_LTCCore |
| SQL Server 版本 | 2019 Enterprise Edition |
| 資料表數量 | 187 個 |
| View 數量 | 70 個 |
| Stored Procedure 數量 | 504 個 |
| Function 數量 | 38 個 |

> 完整連線資訊請參見 [MSSQL Connection Infomation.md](../../MSSQL%20Connection%20Infomation.md)

---

## Schema 分布統計

| Schema | 表數量 | 用途 |
|--------|--------|------|
| **code** | 37 | 代碼表（字典、配置） |
| **data** | 39 | 業務數據表（核心實體） |
| **join** | 67 | 關聯表（多對多、連接表） |
| **dbo** | 44 | 系統表、暫存表、配置 |
| **總計** | **187** | |

---

## ORM 對照結果

### EF Core Entity vs 資料庫

| 指標 | 數值 |
|------|------|
| Entity 總數 | 104 個 |
| 覆蓋率 | 95%+ |
| 狀態 | **完全對齊** |

**缺失表**（非必要）：
- 暫存表：TempAllCaseList, TempPartner, TempUpdateLog
- 系統表：DownloadLogs, DBVersionUpdateHistory
- 擴展功能：ForumList, ForumReply, CompanyList

### Prisma Schema vs 資料庫

| 指標 | 數值 |
|------|------|
| Model 總數 | 158 個 |
| 覆蓋率 | 82% |
| 狀態 | **部分對齊** |

**各 Schema 覆蓋率**：
| Schema | 表數 | Prisma Model | 覆蓋率 |
|--------|------|--------------|--------|
| code | 37 | 34 | 92% |
| data | 39 | 31 | 79% |
| join | 67 | 60 | 90% |
| dbo | 44 | 33 | 75% |

---

## Views 清單（70 個）

### 合約相關

| View 名稱 | 說明 |
|-----------|------|
| view.Contract | 合約主視圖 |
| view.ContractAttachment | 合約附件 |
| view.ContractHistory | 合約歷程 |
| view.ContractPartner | 合約相對人 |
| view.ContractExaminer | 合約審核人 |
| view.ContractExtendInfo | 合約延伸資訊 |
| view.ContractPriority | 合約優先級 |

### 使用者權限

| View 名稱 | 說明 |
|-----------|------|
| view.User | 使用者 |
| view.UserAuthority | 使用者權限 |
| view.UserContractAuthority | 使用者合約權限 |
| view.Department | 部門 |
| view.DepartmentTreeLevel | 部門樹結構 |
| view.Role | 角色 |
| view.RoleAuthority | 角色權限 |

### 流程管理

| View 名稱 | 說明 |
|-----------|------|
| view.ExamStatus | 審核狀態 |
| view.ContractFlowStageView | 合約流程階段 |

### 代理

| View 名稱 | 說明 |
|-----------|------|
| view.Acting | 代理 |
| view.ActingAgent | 代理人 |
| view.ActingContract | 代理合約 |
| view.ActingEntry | 代理項目 |
| view.AllActing | 所有代理 |

### 通知/事件

| View 名稱 | 說明 |
|-----------|------|
| view.Event | 事件 |
| view.EventAttachment | 事件附件 |
| view.EventContract | 事件合約 |
| view.AlertMailList | 提醒郵件列表 |

### 其他

| View 名稱 | 說明 |
|-----------|------|
| view.Partner | 相對人 |
| view.Project | 專案 |
| view.SignRequirement | 簽署要求 |
| view.UrgentLevel | 緊急程度 |
| view.MainContractType | 主合約類型 |
| view.SubContractType | 子合約類型 |
| view.Attachment | 附件 |
| view.LatestAttachment | 最新附件 |
| view.FileType | 檔案類型 |
| view.CombinedField | 合併欄位 |

---

## Stored Procedures 清單（504 個）

### 核心業務 SP（PRC_ 前綴）- 49 個

#### 合約相關

| SP 名稱 | 用途 |
|---------|------|
| PRC_AllocateContractExaminer | 分配合約審核人 |
| PRC_AutoExtendContract | 自動延期合約 |
| PRC_CloseContractOnSignStage | 簽署階段結案 |
| PRC_ExamineContractSignStage | 審核簽署階段 |
| PRC_ExamineContractStage | 審核合約階段 |
| PRC_DeleteAllContract | 刪除所有合約 |
| PRC_DeleteByContractID | 依ID刪除合約 |
| PRC_InsertContractFlow | 新增合約流程 |
| PRC_UpdateContractWithPartner | 更新合約與相對人 |

#### 單據編號

| SP 名稱 | 用途 |
|---------|------|
| PRC_CheckApplyNo | 檢查申請號 |
| PRC_GetNewApplyNo | 取得新申請號 |
| PRC_CheckReceiveNo | 檢查收件號 |
| PRC_GetNewReceiveNo | 取得新收件號 |
| PRC_CheckSaveNo | 檢查結案號 |
| PRC_GetNewSaveNo | 取得新結案號 |
| PRC_GetNewTransferNo | 取得新移轉號 |
| PRC_GetNewAccessApplyNo | 取得新調閱申請號 |

#### 代理/權限

| SP 名稱 | 用途 |
|---------|------|
| PRC_GetActedByContractID | 依合約ID取得代理 |
| PRC_GetAllLineManagerByUserId | 取得所有直屬主管 |
| PRC_UserContractAuthorityForDepartment | 部門合約權限 |
| PRC_GetDepartmentChief | 取得部門主管 |
| PRC_GetLineManagerChief | 取得直屬主管 |
| PRC_GetLineManagersIdToRoot | 取得至根的主管ID |
| PRC_GetFinalApprover | 取得最終核准人 |

#### 審查流程

| SP 名稱 | 用途 |
|---------|------|
| PRC_GetExamFlowStage | 取得審查流程階段 |
| PRC_GetExamStatusListByStageID | 依階段取得狀態列表 |
| PRC_GetExaminerAuthorityStage | 取得審核人權限階段 |
| PRC_GetMyContractByStageID | 依階段取得我的合約 |
| PRC_GetFlowWithDirectorStage | 取得含主管的流程 |
| PRC_GetDefaultExaminerByContractFlowID | 取得預設審核人 |
| PRC_GetAssignCaseDefaultReviewer | 取得分案預設審核人 |

### 標準 CRUD SP（SP_ 前綴）- 122+ 個

**模式**：`SP_[EntityName]_[Operation]Command`

| Operation | 數量 | 說明 |
|-----------|------|------|
| _InsertCommand | 35+ | 新增資料 |
| _UpdateCommand | 35+ | 更新資料 |
| _DeleteCommand | 30+ | 刪除資料 |
| _SelectCommand | 30+ | 查詢資料 |
| _PagedList_SelectCommand | 15+ | 分頁查詢 |
| _Sorted_PagedList_SelectCommand | 10+ | 排序分頁查詢 |
| _Count_SelectCommand | 8+ | 計數查詢 |

**涵蓋實體**：
User, UserRole, UserAuthority, Contract, ContractAmount, ContractExaminer, Attachment, Partner, Department, OtherExaminer, ActingAgent, UsingLog, MessageLogs, MailLog 等

### 報表 SP（M_ 前綴）- 12 個

| SP 名稱 | 用途 |
|---------|------|
| M_Detail_ContractData | 合約資料詳情 |
| M_Detail_ContractHistory | 合約歷程詳情 |
| M_Detail_ContractTypeList | 合約類型列表 |
| M_Detail_SignHistory | 簽署歷程詳情 |
| M_General_MonthlyContract | 月度合約統計 |
| M_STA_CaseCountByApplicantDepartment | 依部門統計 |
| M_STA_CaseCountByStage | 依階段統計 |
| M_STA_CaseCountByUrgentLevel | 依緊急程度統計 |
| M_STA_CaseCountByYear | 依年度統計 |

### 權限檢查 SP

| SP 名稱 | 用途 |
|---------|------|
| CheckContractPermission | 合約權限檢查（核心） |
| CheckExistsEmpolyeeANDLoginID | 檢查員工與登入ID |
| CheckExistsSubDepartment | 檢查子部門存在 |

### Functions（38 個）

| Function 名稱 | 用途 |
|---------------|------|
| dbo.ValidateAuthority | 驗證使用者權限（核心） |
| dbo.GetDepartmentByUserID | 取得使用者部門 |
| dbo.GetSubDepartmentByDepartmentID | 取得子部門 |
| dbo.GetAuthorityIdFromDepartmentByUserId | 取得部門權限ID |

---

## 資料表分類

### 核心業務表

#### 合約相關（data schema）

| 資料表 | 說明 |
|--------|------|
| Contract | 合約主表 |
| ContractCustom | 合約自訂欄位 |
| ContractExtendInfo | 合約延伸資訊 |
| ContractAmount | 合約金額 |
| ContractExaminer | 合約審核人 |
| ContractHistory | 合約歷程 |
| ContractPartner | 合約相對人 |
| Attachment | 附件 |
| Partner | 相對人 |
| Project | 專案 |

#### 組織與使用者（data/join schema）

| 資料表 | 說明 |
|--------|------|
| User | 使用者 |
| Department | 部門 |
| UserDepartment | 使用者部門關聯 |
| UserRole | 使用者角色 |
| UserAuthority | 使用者權限 |
| UserContractAuthority | 使用者合約權限 |
| UserContractAuthorityForDepartment | 使用者部門合約權限 |

#### 流程配置（code schema）

| 資料表 | 說明 |
|--------|------|
| Authority | 權限定義 |
| AuthorityGroup | 權限群組 |
| ExamStage | 審核階段 |
| ExamStatus | 審核狀態 |
| ExamResult | 審核結果 |
| ContractType | 合約類型 |
| ContractFlow | 合約流程 |
| ContractFlowStage | 合約流程階段 |

### 完整資料表清單

<details>
<summary>點擊展開全部 187 個資料表</summary>

```
_dbSchema
_dbSchema2
_temp_ContractCustomizedField
_tempViewContract
_Test
ActingAgent
ActingContract
ActingEntry
ApiLog
Attachment
AttachmentBIP
AttachmentCertified
AttachmentGuid
AttachmentWatermark
Authority
AuthorityChangeLog
AuthorityGroup
Classification
CloseStage
CloseStatus
CompanyList
Contract
contract_附件
ContractAccessRelated
ContractAccessType
ContractAmount
ContractAttachment
ContractAttachmentChange
ContractAttachmentStatus
ContractClassification
ContractCurrentExaminerTemp
ContractCustom
ContractCustomizedField
ContractCustomizedFieldForSearch
ContractDataChange
ContractEnvelopes
ContractEvent
ContractExaminer
ContractExaminerChange
ContractExamStageInfo
ContractExtendInfo
ContractFileTemplate
ContractFileTemplateAttachment
ContractFileTemplateDepartmentAuthority
ContractFileTemplateExtraAttachment
ContractFileTemplateType
ContractFileTemplateUserAuthority
ContractFlow
ContractFlowCSDefaultDepartment
ContractFlowCSDefaultExaminer
ContractFlowCSDefaultStage
ContractFlowDefaultDepartment
ContractFlowDefaultExaminer
ContractFlowDefaultSyncStage
ContractFlowStage
ContractGuid
ContractHistory
ContractLog
ContractMailLog
ContractMessageBoard
ContractModule
ContractNoCloseNotice
ContractOtherNotify
ContractPartner
ContractRequireAttribute
ContractRequireSign
ContractStampDuty
ContractType
ContractType_Language
ContractTypeDepartment
ContractViewTemp
CountryCode
CSExamResult
CSExamResultLanguage
CustomExtendField
CustomizeField
DBVersionUpdateHistory
Department
DepartmentTemp
DirectorRule
Domain
DownloadLogs
DraftContract
EnvelopeAttachment
EnvelopeInfo
EnvelopeStage
Event
EventAttachment
EventSendMailExamStageList
EventSendMailList
EventSendMailOtherRolesList
EventSendOtherMailList
EventStatus
ExaminerGroup
ExamResult
ExamRule
ExamStage
ExamStageAuthority
ExamStageConfig
ExamStatus
ExamStatusLanguage
Exchange
FileType
ForumList
ForumReply
ForumTopicReply
LoginLog
LTCLog
MailLog
MailLogType
MailType
MainContractDepartment
MainContractType
MainContractType_Language
Memo
MessageBoard
MessageBoardConfig
MessageLogs
Messages
OtherContractAttachmentStatus
OtherExaminer
OtherExaminerAttachment
OtherExaminerConfig
OtherExaminerConfigAttachment
OTPToken
Partner
PartnerContact
PartnerSignLog
Project
ProjectApplicant
ProjectContract
ProjectEvent
ProjectType
RelatedContract
Result
SerialNumber
SignAttachment
SignAttachmentInfo
SignRequirement
SignRequirementGroup
SiteCode
SNStore
SQL_UpdateList
StampDuty
SyncStage
SystemLanguage
TEMP
TempAllCaseList
TempPartner
TempUpdateLog
TransferCaseLog
tt2
UpdateRevision
UrgentLevel
User
UserAuthority
UserColumnPreference
UserComment
UserContractAuthority
UserContractAuthorityForDepartment
UserDepartment
UserIdentity
UserListPreference
UserRole
UsingLog
Webconfig
```

</details>

---

## 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2026-01-21 | 建立文件框架，列出資料表清單 |
| 2026-01-21 | 新增 Schema 分布統計、ORM 對照結果、View/SP 清單 |
