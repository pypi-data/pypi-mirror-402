# 兩套系統資料存取差異分析

## 概述

本文件記錄 ECS 後台系統（ecscore-master）與前台系統（ecs-ten-main）在資料存取上的差異，為 MCP 開發提供參考。

---

## 一、Repository 規模對比

| 指標 | 後台 (ecscore) | 前台 (ecs-ten) |
|------|---------------|----------------|
| Repository 總數 | 89 個 | 51 個 |
| 含客製化 | +15 個 | - |
| **共同 Repository** | 19 個 | 19 個 |
| **僅此系統有** | 40 個 | 12 個 |

---

## 二、Repository 分類

### 共同 Repository（19 個）

兩套系統都有的基礎功能：

| 功能 | 後台 | 前台 |
|------|------|------|
| 合約 | ContractRepository | contract-repository |
| 合約審核人 | ContractExaminerRepository | contract-examiner-repository |
| 合約歷程 | ContractHistoryRepository | contract-history-repository |
| 合約附件 | ContractAttachmentRepository | contract-attachment-repository |
| 使用者 | UserRepository | user-repository |
| 部門 | DepartmentRepository | department-repository |
| 相對人 | PartnerRepository | partner-repository |
| 專案 | ProjectRepository | project-repository |
| 附件 | AttachmentRepository | attachment-repository |
| 會辦 | OtherExaminerRepository | other-examiner-repository |

### 僅後台有的 Repository（40 個）

#### 系統管理類
| Repository | 用途 |
|------------|------|
| UserManager | 使用者管理（管理員專屬） |
| Webconfig | 系統配置 |
| ApiLog | API 日誌 |

#### 報表分析類
| Repository | 用途 |
|------------|------|
| ReportRepository | 資料分析報表 |

#### 審核配置類
| Repository | 用途 |
|------------|------|
| ExamFlowStage | 審核流程階段配置 |
| MailRepository | 郵件配置 |

#### 客製化類（15 個）
| 前綴 | 說明 |
|------|------|
| W01, N01... | 公司特定業務邏輯 |

### 僅前台有的 Repository（12 個）

| Repository | 用途 | 特性 |
|------------|------|------|
| **draft-contract** | 草稿管理 | 使用者可保存未提交合約 |
| **acting-contract** | 代理合約 | 使用者可代理他人操作 |
| **online-accessible** | 權限過濾 | **最重要** - 權限感知的合約列表 |
| **smart-contract** | 智能合約 | AI 功能（新一代） |
| contract-list | 合約列表 | 前台優化查詢 |
| contract-access | 合約調閱 | 前台專用 |

---

## 三、權限控制差異

### 後台（ecscore）- 存儲過程級權限控制

```
API Layer → Stored Procedure (UserID + Type 參數)

SP_Contract_Sorted_PagedList_SelectCommand
├─ Type=1: 全公司（管理員）
├─ Type=2: 部門
├─ Type=3: 待審
├─ Type=4: 我的合約
├─ Type=5: 特許案件
└─ Type=6: 代理案件
```

**特點**：
- 權限邏輯在資料庫層
- 難以篡改
- 難以維護和測試

### 前台（ecs-ten）- 應用層多級權限控制

```
Route → Service → Repository → Prisma ORM

├─ requireAuth 中間件 (JWT 驗證)
├─ Service 層權限檢查 (ForbiddenError)
└─ online-accessible-contract-repository (權限過濾)
```

**特點**：
- 權限邏輯集中管理
- 易於測試
- 易於維護

### 權限檢查位置對比

| 檢查點 | 後台 | 前台 |
|--------|------|------|
| 認證 | Cookie/Session | JWT Token |
| 功能權限 | Middleware | Middleware |
| 資料過濾 | Stored Procedure | Repository/Service |
| 合約權限 | SP 參數 Type | PermissionService |

---

## 四、資料存取模式

### 合約列表查詢

**後台**：
```csharp
// 調用 Stored Procedure
SP_Contract_Sorted_PagedList_SelectCommand
  @UserID, @Type, @PageSize, @PageIndex...
```

**前台**：
```typescript
// Prisma ORM + 權限過濾
const contracts = await prisma.contract.findMany({
  where: {
    ...permissionFilter,  // 動態權限條件
    ...userFilter         // 使用者條件
  }
})
```

### 敏感資料存取規則

| 資料類型 | 後台 | 前台 |
|----------|------|------|
| 財務資料 | 無限制 | 權限過濾 |
| 簽署資訊 | 全看 | 僅簽署者/審核者 |
| 使用者資訊 | 管理級 | 基本資訊 |
| 草稿資料 | 無 | 所有者私密 |

---

## 五、MCP 開發建議

### 功能選擇端點

| 功能 | 建議端點 | 原因 |
|------|---------|------|
| 合約列表（使用者） | **前台** | 已有權限過濾 |
| 合約詳情 | **前台** | 權限檢查 |
| 草稿管理 | **前台** | 僅前台有 |
| 報表資料 | **後台** | 僅後台有 |
| 系統配置 | **後台** | 僅後台有 |
| 使用者管理 | **後台** | 管理員權限 |

### 關鍵 Repository

| 優先級 | Repository | 系統 | 說明 |
|--------|-----------|------|------|
| 1 | online-accessible-contract-repository | 前台 | 權限感知合約查詢 |
| 2 | contract-list-repository | 前台 | 合約列表查詢 |
| 3 | ContractListRepository + SP | 後台 | 管理員合約查詢 |
| 4 | contract-repository | 前台 | 基礎 CRUD |

### 安全建議

```
優先級 1: 使用前台 API（已有權限控制）
優先級 2: 管理員操作用後台 API（無權限限制）
優先級 3: 對敏感資料始終驗證 JWT 中的 userId
```

---

## 六、性能特性

| 特性 | 後台 | 前台 |
|------|------|------|
| 查詢優化 | SQL 層 + 存儲過程 | ORM 查詢 |
| 編譯模型 | EF Core Compiled Models | 無 |
| 權限過濾 | SP 內部 | 應用層 |
| 複雜查詢 | 存儲過程 | Raw SQL |
| 測試性 | 較難 | 較易 |

---

## 七、關鍵檔案位置

### 後台（ecscore-master）

| 類別 | 路徑 |
|------|------|
| Repository | `lib/Ltc.EcsDB/Repositories/` |
| Stored Procedure | `db.schema/06.storedprocedures/` |
| 權限 SP | `db.schema/06.storedprocedures/dbo.CheckContractPermission.sql` |

### 前台（ecs-ten-main）

| 類別 | 路徑 |
|------|------|
| Repository | `packages/ecs-ten-server/src/repositories/` |
| Service | `packages/ecs-ten-server/src/services/` |
| 權限服務 | `packages/ecs-ten-server/src/services/permission-service.ts` |
| 權限過濾 | `packages/ecs-ten-server/src/repositories/online-accessible-contract-repository.ts` |
