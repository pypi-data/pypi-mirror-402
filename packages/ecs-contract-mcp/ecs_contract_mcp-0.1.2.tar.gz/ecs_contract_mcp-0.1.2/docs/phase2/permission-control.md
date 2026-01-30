# 權限控制機制分析

## 概述

本文件記錄 ECS 系統的權限控制機制，包括三層授權體系、角色機制、合約權限過濾等。

---

## 一、權限模型結構

### 核心資料表關係

```
┌─────────────────────────────────────────────────────────────────┐
│                      權限系統架構圖                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [code].[Authority]  (權限定義表)                               │
│  ├─ AuthorityID      (權限ID)                                   │
│  ├─ Name             (權限名稱)                                 │
│  ├─ GroupID          (所屬權限群組)                             │
│  └─ Disable          (停用標記)                                 │
│       │                                                         │
│       ├─→ [code].[AuthorityGroup] (權限群組)                   │
│       │   ├─ GroupID              (群組ID)                     │
│       │   └─ ExamStageID          (審查階段)                   │
│       │                                                         │
│       └─→ [join].[UserAuthority] (使用者權限對應)             │
│           ├─ UserID      (使用者ID)                            │
│           └─ AuthorityID (權限ID)                              │
│                                                                  │
│  [join].[UserRole] (使用者角色映射)                            │
│  ├─ UserID      (使用者ID)                                     │
│  └─ RoleUserID  (角色User ID)                                  │
│                                                                  │
│  [join].[UserContractAuthority] (合約級別權限)                │
│  ├─ UserID      (使用者ID)                                     │
│  ├─ ContractID  (合約ID)                                       │
│  └─ AuthorityID (權限ID)                                       │
│                                                                  │
│  [join].[UserContractAuthorityForDepartment] (部門合約權限)    │
│  ├─ UserID      (使用者ID)                                     │
│  ├─ DepartmentID (部門ID)                                      │
│  └─ AuthorityID  (權限)                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、三層授權體系

### 第一層：系統級權限 (Universal Permissions)

存儲在 `[join].[UserAuthority]` 表中，直接分配給使用者。

**權限ID對照表**：

| 權限範圍 | ID | 說明 |
|---------|-----|------|
| 超級管理員 | 1 | 最大權限 |
| **合約管理（後台）** | 2001-2012 | |
| - 新申請案 | 2001 | |
| - 待審案件 | 2002 | |
| - 我的案件 | 2003 | |
| - 部門案件 | 2004 | |
| - 特許案件 | 2005 | |
| - 所有案件 | 2006 | |
| - 代理案件 | 2007 | |
| - 我的未結案 | 2008 | |
| - 我的結案 | 2009 | |
| - 暫存案件 | 2010 | |
| - 待審(批次核准) | 2011 | |
| - 特許(依部門) | 2012 | |
| **合約調閱（前台）** | 1201-1207 | |
| - 新申請案 | 1201 | |
| - 待審案件 | 1202 | |
| - 部門案件 | 1203 | |
| - 所有案件 | 1204 | |
| - 我的未結案 | 1205 | |
| - 我的結案 | 1206 | |
| - 線上調閱 | 1207 | |
| **審核階段角色** | 51002-62002 | |
| - 申請人 | 51002 | |
| - 主管審核 | 52002 | |
| - 法務分案 | 53002 | |
| - 法務初審 | 54002 | |
| - 法務審核 | 55002 | |
| - 法務主管審核 | 56002 | |
| - 最終核准人 | 57002 | |
| - 簽署用印 | 58002 | |
| - 會辦單位 | 60002 | |
| - 結案歸檔 | 61002 | |
| - 申請人結案 | 62002 | |
| - Docusign簽署 | 995102 | |
| **文件權限** | 9001-9002 | |
| - 檢視結案文件 | 9001 | |
| - 下載結案文件 | 9002 | |

### 第二層：合約特定權限 (Contract-Level)

存儲在 `[join].[UserContractAuthority]` 表中。

- **用途**：為特定合約分配特殊權限給使用者
- **結構**：`(UserID, ContractID, AuthorityID)`
- **場景**：某使用者對某合約有「特許案件」權限

### 第三層：部門級別權限 (Department-Level)

存儲在 `[join].[UserContractAuthorityForDepartment]` 表中。

- **用途**：以部門為單位授予權限
- **結構**：`(UserID, DepartmentID, AuthorityID)`
- **場景**：法務經理可查看法務部門所有「特許案件」

---

## 三、角色機制

### Role 定義

**Role 是一個「虛擬使用者」概念**：

```
[data].[User] 表
├─ Role = 0  → 實際使用者
└─ Role = 1  → 角色（虛擬容器，存放權限集合）
```

### 使用者-角色映射

```
[join].[UserRole] 表
├─ UserID      (實際使用者ID)
├─ RoleUserID  (角色的User ID)
└─ SystemDefine
```

**權限查詢邏輯**：
1. 查詢使用者的直接權限
2. 查詢使用者關聯的角色
3. 查詢角色的所有權限
4. 合併返回

### ValidateAuthority SQL 函數

```sql
-- 位置：/db.schema/04.functions/dbo.ValidateAuthority.sql
IF EXISTS(
  -- 直接權限
  SELECT 1 FROM [join].UserAuthority
  WHERE UserID = @UserID AND AuthorityID = @AuthorityID
  UNION
  -- 角色繼承權限
  SELECT 1 FROM [join].UserRole ur
  INNER JOIN [join].UserAuthority ua ON ur.RoleUserID = ua.UserID
  WHERE AuthorityID = @AuthorityID AND ur.UserID = @UserID
)
```

---

## 四、合約權限控制

### 合約類型過濾規則

| Type | 名稱 | 過濾邏輯 |
|------|------|---------|
| 1 | 全公司合約 | 所有合約 |
| 2 | 部門案件 | 申請人部門符合使用者部門（含祖先部門） |
| 3 | 待審案件 | 複雜分案邏輯、會辦案件 |
| 4 | 我的案件 | 審核人/填表人/分案人是登入者 |
| 5 | 特許案件 | 存在於 UserContractAuthority |
| 6 | 代理案件 | 代理他人的案件 |
| 7 | 我的未結案 | 狀態為未結案 |
| 8 | 我的結案 | 狀態為已結案 |
| 10 | 暫存案件 | 暫存中 |
| 11 | 批次審理 | 支援批次核准 |
| 12 | 特許(依部門) | 基於 UserContractAuthorityForDepartment |

### 權限ID對應

| 權限ID | Type |
|--------|------|
| 2002/1202 | 待審案件 (3) |
| 2004/1203 | 部門案件 (2) |
| 2006/1204 | 所有案件 (1) |
| 2003/1205 | 我的案件 (4) |
| 2005 | 特許案件 (5) |
| 2007 | 代理案件 (6) |
| 2008/1205 | 我的未結案 (7) |
| 2009/1206 | 我的結案 (8) |

---

## 五、前台權限服務

### PermissionService 主要方法

```typescript
// 取得使用者所有權限
getUserPermissions(userId: number): UserPermissionsResult

// 檢查單一權限
hasUserPermission(userId: number, permission: UserPermissionType): boolean

// 檢查任一權限
hasAnyUserPermission(userId: number, permissions: UserPermissionType[]): boolean

// 取得合約級別權限
getContractPermissions(userId: number, contractGuid: string): ContractPermission

// 自訂條件檢查
hasAnyContractPermissionWithFilter(
  userId: number,
  contractGuid: string,
  permissionFilters: PermissionFilters
): boolean
```

### 合約權限物件

```typescript
interface ContractPermission {
  examinerPermissions?: ExaminerPermissionResult[]  // 審核人權限
  viewerPermissions?: ViewerPermissionResult[]      // 檢視人權限
  adminPermissions?: AdminPermissionResult[]        // 管理員權限
}
```

---

## 六、部門層級支援

### 部門層級結構

```
[data].[Department] 表
├─ DepartmentID
└─ ParentID (遞歸層級)
```

### CTE 遞歸查詢

```sql
WITH T AS (
  SELECT DepartmentID, ParentID, 1 AS Level
  FROM data.Department
  WHERE DepartmentID IN (SELECT DepartmentID FROM #UserDept)
  UNION ALL
  SELECT a.DepartmentID, a.ParentID, T.Level + 1 AS Level
  FROM data.Department a
  INNER JOIN T ON a.ParentID = T.DepartmentID
)
```

---

## 七、驗權流程

```
使用者訪問合約
    ↓
[驗證認證] - JWT Token
    ↓
[檢查功能權限] - hasUserPermission()
    ├─ 查詢直接權限
    ├─ 查詢角色權限
    └─ 返回 true/false
    ↓
[過濾可見合約列表]
    ├─ 調用 CheckContractPermission SP
    └─ 根據 listType 和 userId 過濾
    ↓
[檢查特定合約權限] - getContractPermissions()
    ├─ examinerPermissions (審核人)
    ├─ viewerPermissions (檢視人)
    └─ adminPermissions (管理員)
    ↓
[決定最終操作權限]
    ├─ 檢視：需要 viewerPermissions
    ├─ 編輯：需要 examinerPermissions
    └─ 管理：需要 adminPermissions
```

---

## 八、關鍵檔案位置

### ecscore-master（後台）

| 類別 | 檔案路徑 |
|------|---------|
| 權限驗證函數 | `db.schema/04.functions/dbo.ValidateAuthority.sql` |
| 合約權限檢查 SP | `db.schema/06.storedprocedures/dbo.CheckContractPermission.sql` |
| 權限定義表 | `db.schema/01.tables/code.Authority.sql` |
| 使用者權限表 | `db.schema/01.tables/join.UserAuthority.sql` |
| 使用者角色表 | `db.schema/01.tables/join.UserRole.sql` |
| 合約權限表 | `db.schema/01.tables/join.UserContractAuthority.sql` |
| 部門權限表 | `db.schema/01.tables/join.UserContractAuthorityForDepartment.sql` |
| 權限中間件 | `WebApp.ECSMobile/Middleware/ContractPermissionMiddleware.cs` |
| Authority Model | `lib/Ltc.EcsDB/Models/Authority.cs` |
| 角色權限視圖 | `db.schema/05.views/view.RoleAuthority.sql` |
| 權限初始化資料 | `db.schema/50.data/_init.DATA.20231025120000.sql` |

### ecs-ten-main（前台）

| 類別 | 檔案路徑 |
|------|---------|
| 認證中間件 | `packages/ecs-ten-server/src/middleware/auth.ts` |
| JWT 中間件 | `packages/ecs-ten-server/src/middleware/jwt.ts` |
| 權限服務 | `packages/ecs-ten-server/src/services/permission-service.ts` |
| 合約列表服務 | `packages/ecs-ten-server/src/services/contract-list-service.ts` |
| 合約列表 Repository | `packages/ecs-ten-server/src/repositories/contract-list-repository.ts` |
| 權限 Schema | `packages/ecs-ten-server/src/schema/permission-schema.ts` |
