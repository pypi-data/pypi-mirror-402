# ECS Ten Prisma 模型詳細清單

> 本文件為 [ecs-ten-analysis.md](ecs-ten-analysis.md) 的補充資料

## Prisma Schema 位置

```
packages/ecs-ten-server/prisma/schema.prisma (4155 行)
```

---

## 四個 Schema 分類

### code Schema（代碼表）- 34 個

用途：字典、配置、參考資料

| Model | 說明 |
|-------|------|
| CodeContractType | 合約類型代碼 |
| CodeContractAmount | 合約金額代碼 |
| ContractTypeLanguage | 合約類型語言 |
| ContractTypeDepartment | 合約類型部門 |
| ExamStage | 審查關卡 |
| ExamResult | 審查結果 |
| ExamStatus | 審查狀態 |
| ExamStatusLanguage | 審查狀態語言 |
| ExamRule | 審查規則 |
| ExamStageAuthority | 關卡權限 |
| ExamStageConfig | 關卡配置 |
| Authority | 權限 |
| AuthorityGroup | 權限群組 |
| Classification | 分類 |
| CloseStage | 結案階段 |
| CloseStatus | 結案狀態 |
| Domain | 網域 |
| Exchange | 匯率 |
| FileType | 檔案類型 |
| MainContractType | 主合約類型 |
| MainContractTypeLanguage | 主合約類型語言 |
| Memo | 備忘 |
| MessageBoard | 留言板 |
| MessageBoardConfig | 留言板配置 |
| Message | 訊息 |
| OtherContractAttachmentStatus | 其他附件狀態 |
| MailLogType | 郵件日誌類型 |
| MailType | 郵件類型 |
| SignRequirement | 簽署需求 |
| SiteCode | 站點代碼 |
| StampDuty | 印花稅 |
| SyncStage | 同步階段 |
| SystemLanguage | 系統語言 |
| UrgentLevel | 緊急程度 |
| DirectorRule | 主管規則 |

---

### data Schema（業務資料）- 31 個

用途：主要業務實體

| Model | 說明 |
|-------|------|
| **Contract** | 合約主表 |
| **User** | 使用者 |
| **Partner** | 相對人 |
| PartnerContact | 相對人聯絡人 |
| **Department** | 部門 |
| DepartmentTemp | 臨時部門 |
| ContractCustom | 合約自訂 |
| ContractCustomizedField | 合約客製欄位 |
| ContractCustomizedFieldForSearch | 可搜尋客製欄位 |
| ContractExtendInfo | 合約延展資訊 |
| ContractEnvelope | 合約信封 |
| ContractHistory | 合約歷程 |
| ContractLog | 合約日誌 |
| ContractMailLog | 合約郵件日誌 |
| Event | 事件 |
| EventAttachment | 事件附件 |
| LoginLog | 登入日誌 |
| LtcLog | LTC 日誌 |
| MailLog | 郵件日誌 |
| UserComment | 使用者評論 |
| UsingLog | 使用日誌 |
| ContractAccessRelated | 合約存取關聯 |
| Project | 專案 |
| ProjectApplicant | 專案申請人 |
| ProjectEvent | 專案事件 |
| Attachment | 附件 |
| AttachmentBip | BIP 附件 |
| AttachmentCertified | 認證附件 |
| AttachmentWatermark | 浮水印附件 |
| AttachmentGuid | 附件 GUID |
| ApiLog | API 日誌 |

---

### join Schema（關聯表）- 60 個

用途：多對多關聯、連接表

**Contract 關聯**：
- JoinContractType, JoinContractAmount
- ContractAttachment, ContractAttachmentStatus
- ContractClassification, ContractCurrentExaminerTemp
- ContractAccessType, ContractMessageBoard
- ContractRequireAttribute, ContractRequireSign
- ContractPartner, ContractExaminer
- ContractExamStageInfo, ContractEvent
- ContractFileTemplate 系列（6 個）
- ContractFlow 系列（7 個）
- ContractGuid, ContractOtherNotify
- ContractModule, ContractNoCloseNotice
- ContractViewTemp, ContractStampDuty
- ContractDataChange, ContractAttachmentChange
- ContractExaminerChange

**User 關聯**：
- UserAuthority, UserContractAuthority
- UserContractAuthorityForDepartment
- UserDepartment, UserRole
- UserColumnPreference, UserListPreference

**其他關聯**：
- ActingAgent, ActingContract, ActingEntry
- EventSendMail 系列（4 個）
- ExaminerGroup, MainContractDepartment
- PartnerSignLog, ProjectContract
- RelatedContract, SerialNumber
- SignAttachment, SignAttachmentInfo
- SnStore, SqlUpdateList

---

### dbo Schema（系統預設）- 33 個

用途：系統預設物件、日誌、配置

包含與其他 schema 重複的核心表（多 schema 映射）

---

## Contract Model 欄位詳細

### 基本資訊
- documentName, documentNo, applyNo
- createDate, recorderId

### 狀態管理
- currentStageId, backStageId, closeStageId

### 日期欄位
- receiveDate, saveDate, applicationDate
- provisionDate, effectiveDate
- validStartDate, validEndDate

### 費用欄位
- cost, costNtd (Decimal 18,2)
- finalCost, finalCostNtd
- exchangeTypeId, finalCostExchangeRate

### 簽署設定
- requireSign, requirePartnerSign
- signTypeId

### 警示設定
- alertExtend, alertBeginDate, alertEndDate
- alertPeriod, alertEmails, alertCcEmails
- notifyBeforeDay, notifyDay

### 自動延期設定
- autoExtend, autoExtendContract
- extendYear, extendMonth
- extendPeriodYear, extendPeriodMonth

### 保留欄位（動態表單）
```
txt01-txt10, memo01-memo15, radio01-radio05,
checkBox01-checkBox05, select01-select05,
int01-int05, double01-double05, date01-date10
```

---

## Repository 清單

位置：`packages/ecs-ten-server/src/repositories/`

### Contract 相關（18 個）
| Repository | 說明 |
|------------|------|
| contract-repository.ts | 核心合約 |
| contract-list-repository.ts | 合約列表 |
| contract-attachment-repository.ts | 合約附件 |
| contract-examiner-repository.ts | 合約審查人 |
| contract-exam-stage-info-repository.ts | 關卡資訊 |
| contract-exam-stage-repository.ts | 審查關卡 |
| contract-history-repository.ts | 合約歷程 |
| contract-partner-repository.ts | 合約相對人 |
| contract-amount-repository.ts | 合約金額 |
| contract-data-change-repository.ts | 資料變更 |
| contract-type-repository.ts | 合約類型 |
| contract-view-temp-repository.ts | 檢視暫存 |
| smart-contract-repository.ts | 智能合約 |

### 其他核心
| Repository | 說明 |
|------------|------|
| user-repository.ts | 使用者 |
| department-repository.ts | 部門 |
| partner-repository.ts | 相對人 |
| attachment-repository.ts | 附件 |
| exam-stage-repository.ts | 審查關卡 |

---

## Service 清單（52 個）

位置：`packages/ecs-ten-server/src/services/`

### Contract 相關
- contract-service.ts
- contract-list-service.ts
- contracts-service.ts
- contract-history-service.ts
- contract-attachment-service.ts
- contract-exam-stage-service.ts
- contract-data-change-service.ts
- contract-access-list-service.ts
- contract-signature-service.ts
- online-accessible-contract-service.ts
- main-contract-type-service.ts

### 其他核心
- auth-service.ts（LDAP 整合）
- permission-service.ts
- archive-service.ts
- attachment-service.ts
- co-examiner-service.ts

---

## 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2026-01-21 | 從 Prisma Schema 探索建立 |
