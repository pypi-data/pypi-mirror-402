# 後台管理系統分析 (ecscore-master)

> 原始碼位置：`reference/ecscore-master/`
>
> 📖 參考文件：`reference/ecscore-master/CLAUDE.md`

## 系統定位

| 項目 | 說明 |
|------|------|
| 角色 | 後台管理系統 |
| 使用者 | 公司管理者、系統管理員 |
| 權限 | 管理者權限，可存取所有資料與設定 |

## 專案概覽

### 技術棧（已確認）

| 項目 | 技術 | 來源 |
|------|------|------|
| 框架 | **ASP.NET Core 8.0 MVC** | CLAUDE.md |
| ORM | **Entity Framework Core 8.0**（使用 Compiled Models） | CLAUDE.md |
| 資料庫 | MSSQL Server 2019 | 連線測試 |
| 前端 | Vue 3 + TypeScript + Element Plus | CLAUDE.md |
| 狀態管理 | Pinia（with persistence） | CLAUDE.md |
| 建構工具 | Vite + Gulp | CLAUDE.md |
| 樣式 | UnoCSS（.tailwind prefix） | CLAUDE.md |
| 國際化 | vue-i18n（zh-Hant, en, ja, zh-Hans） | CLAUDE.md |

### 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                    ECS Core 系統架構                         │
├─────────────────────────────────────────────────────────────┤
│  前端層 (Vue 3 SPA)                                          │
│  webapp.ecs2009.client/ → 掛載到 .lt-page-content           │
├─────────────────────────────────────────────────────────────┤
│  頁面層 (Razor Pages + Vue 混合)                             │
│  WebApp.ECS2009/Pages/{area}/{page}.cshtml                  │
│  - 認證授權 (validateAuthority)                              │
│  - 傳遞資料 (window.pageArgs)                                │
├─────────────────────────────────────────────────────────────┤
│  API 層                                                      │
│  packages/webapp.apicore/ → RESTful API                     │
├─────────────────────────────────────────────────────────────┤
│  業務邏輯層                                                   │
│  lib/Ltc.EcsCode/                                           │
├─────────────────────────────────────────────────────────────┤
│  資料存取層                                                   │
│  lib/Ltc.EcsDB/ → EcsDbContext (新) + EcsDataContext (舊)   │
├─────────────────────────────────────────────────────────────┤
│  資料庫 (SQL Server 2019)                                    │
│  + Stored Procedures (db.schema/)                           │
└─────────────────────────────────────────────────────────────┘
```

### 專案結構

```
ecscore-master/
├── lib/                          # 核心程式庫
│   ├── Ltc.Common/              # 共用工具
│   ├── Ltc.EcsCode/             # ECS 核心邏輯
│   ├── Ltc.EcsDB/               # 資料庫存取層 ⭐ 重點分析
│   ├── Ltc.EcsModel/            # 資料模型 ⭐ 重點分析
│   └── Ltc.Customization/       # 客製化功能
├── packages/
│   └── webapp.apicore/          # API 核心
├── webapp.ecs2009.client/        # Vue 3 前端 SPA
├── WebApp.ECS2009/              # 主要 Web 應用 (Razor Pages)
│   ├── Pages/                   # Razor 頁面
│   └── Customization/{company}/ # 公司別客製化
├── WebApp.ECSMobile/            # 行動版 Web 應用
├── WebApp.ECSTools/             # 工具應用
└── db.schema/                   # 資料庫 Schema（依賴順序遷移）
```

### 多租戶客製化機制

系統支援公司別客製化：
- **設定檔**：`WebApp.ECS2009/Customization/{company}/configs/`
- **Controller**：公司專屬 Controller 實作
- **前端**：公司專屬 Vue 元件和頁面
- **資源**：公司專屬本地化資源
- **切換指令**：`just set-configs {company}`

### 認證機制

| 方式 | 說明 |
|------|------|
| Cookie Authentication | 主要認證方式 |
| Azure AD / OpenID Connect | 可設定 |
| API Key | 外部整合用 |
| OA WebAuthn | 無密碼認證 |
| OA Krb | Kerberos 整合 |
| Passthrough Login | 外部 JWT → Cookie Session |

## Entity 模型

> 📖 完整清單請見：[ecscore-entities.md](ecscore-entities.md)

### 統計

| 項目 | 數量 |
|------|------|
| Entity 類別 | **104 個** |
| ViewModels | 127+ 個 |
| Compiled Models | 127+ 個 |

### 檔案位置

| 類型 | 位置 |
|------|------|
| DbContext | `lib/Ltc.EcsDB/EcsDbContext.cs` |
| Entity 類別 | `lib/Ltc.EcsDB/Models/` |
| Partial 類別 | `lib/Ltc.EcsDB/PartialModels/` |
| ViewModels | `lib/Ltc.EcsDB/ViewModels/` |
| Repositories | `lib/Ltc.EcsDB/Repositories/` |

### DbContext

| Context | 技術 | 說明 |
|---------|------|------|
| **EcsDbContext** | EF Core 8.0 | 新式，主要使用 |
| EcsDataContext | LINQ to SQL | 舊式，遺留支援 |

### 核心 Entity 分類

| 分類 | 核心 Entity |
|------|-------------|
| 合約主體 | Contract, ContractType, MainContractType |
| 審查流程 | ExamStage, ExamStatus, ContractExaminer, ContractHistory |
| 使用者權限 | User, Department, Role, Authority |
| 相對人 | Partner, PartnerContact, ContractPartner |
| 附件 | Attachment, ContractAttachment |
| 簽署 | SignRequirement, EnvelopeInfo |
| 事件通知 | Event, MailLog |

### Contract 保留欄位（動態表單）

```
Txt01-10, Memo01-15, Radio01-05, CheckBox01-05,
Select01-05, Int01-05, Double01-05, Date01-10
```

## Repository 層

### Repository 位置

`lib/Ltc.EcsDB/Repositories/`

### 主要 Repository

| Repository | 負責功能 |
|------------|----------|
| ContractRepository | 合約 CRUD |
| UserRepository | 使用者管理 |
| DepartmentRepository | 部門管理 |
| ContractHistoryRepository | 合約歷程 |
| ExamStageRepository | 審查關卡 |

## 核心業務邏輯

> 詳細分析請見獨立文件：

| 主題 | 文件 |
|------|------|
| 合約生命週期 | [business-logic-contract.md](business-logic-contract.md) |
| 審核流程 | [business-logic-approval.md](business-logic-approval.md) |
| 權限控制機制 | [permission-control.md](permission-control.md) |
| 兩套系統差異 | [system-access-diff.md](system-access-diff.md) |

## 重要程式碼片段

### 資料庫連線設定

位置：`WebApp.ECS2009/Customization/ltc/configs/appsettings.lt.json`

```json
{
  "ConnectionStrings": {
    "ecs": "Data Source=ecs2022.ltc;Initial Catalog=LT_ECS_LTCCore;...",
    "LTImportConnectionString": "...",
    "CustomConnectionString": "..."
  }
}
```

## 待研究項目

- [x] ~~DbContext 設定與使用方式~~ → EcsDbContext（新）+ EcsDataContext（舊）
- [x] ~~Entity 與資料表的對應關係~~ → 104 個 Entity，已分類整理
- [x] ~~Repository Pattern 實作細節~~ → 位於 lib/Ltc.EcsDB/Repositories/
- [x] ~~API 認證與授權機制~~ → 已從 CLAUDE.md 取得概覽
- [x] ~~合約狀態流轉邏輯~~ → 見 [business-logic-contract.md](business-logic-contract.md)
- [x] ~~審核流程實作~~ → 見 [business-logic-approval.md](business-logic-approval.md)
- [x] ~~Compiled Models 機制~~ → 位於 lib/Ltc.EcsDB/CompiledModels/

---

## 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2026-01-21 | 建立文件框架 |
| 2026-01-21 | 從 CLAUDE.md 補充技術棧、架構圖、認證機制、多租戶機制 |
| 2026-01-21 | 完成 Entity 模型探索（104 個），建立 ecscore-entities.md |
