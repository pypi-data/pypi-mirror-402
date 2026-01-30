# 前台使用者系統分析 (ecs-ten-main)

> 原始碼位置：`reference/ecs-ten-main/`
>
> 📖 參考文件：
> - `reference/ecs-ten-main/CLAUDE.md`
> - `reference/ecs-ten-main/packages/ecs-ten-server/CLAUDE.md`

## 系統定位

| 項目 | 說明 |
|------|------|
| 角色 | 前台使用者系統 |
| 使用者 | 公司一般員工（非管理者） |
| 權限 | 一般使用者權限，依角色過濾資料 |

## 專案概覽

### 技術棧（已確認）

| 項目 | 技術 | 來源 |
|------|------|------|
| Runtime | **Bun** | CLAUDE.md |
| 後端框架 | **Express.js + TypeScript** | CLAUDE.md |
| ORM | **Prisma**（MS SQL Server） | CLAUDE.md |
| 驗證 | TypeBox（從 OpenAPI 生成） | CLAUDE.md |
| 認證 | JWT + RSA + LDAP | CLAUDE.md |
| 日誌 | Bunyan（structured logging） | CLAUDE.md |
| 格式化 | Biome + Prettier | CLAUDE.md |

### 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                 ecs-ten-main 系統架構                        │
├─────────────────────────────────────────────────────────────┤
│  Routes 層 (src/routes/)                                    │
│  - HTTP 請求處理，無業務邏輯                                  │
│  - parseData() + TypeBox 驗證                               │
├─────────────────────────────────────────────────────────────┤
│  Services 層 (src/services/)                                │
│  - 業務邏輯層                                                │
│  - 可使用 Prisma transactions                               │
│  - 不可直接使用 Prisma Client（需透過 Repository）           │
├─────────────────────────────────────────────────────────────┤
│  Repositories 層 (src/repositories/)                        │
│  - 資料存取層                                                │
│  - 接收 ExtendedPrismaClient                                │
│  - 不可使用 transactions                                    │
├─────────────────────────────────────────────────────────────┤
│  Data Mappers (src/data-mapper/)                            │
│  - DTO 轉換                                                  │
│  - 繼承 SimpleDTOMapper                                     │
├─────────────────────────────────────────────────────────────┤
│  Prisma ORM                                                 │
│  - 4 個 Schema: code, data, dbo, join                       │
│  - prisma/schema.prisma                                     │
├─────────────────────────────────────────────────────────────┤
│  SQL Server 資料庫                                           │
└─────────────────────────────────────────────────────────────┘
```

### 專案結構

```
ecs-ten-main/
├── packages/
│   └── ecs-ten-server/           # 主要後端服務 ⭐ 重點分析
│       ├── src/
│       │   ├── routes/           # HTTP 路由
│       │   ├── services/         # 業務邏輯
│       │   ├── repositories/     # 資料存取
│       │   ├── data-mapper/      # DTO 轉換
│       │   ├── utils/            # 工具函數
│       │   └── prisma-client.ts  # Prisma 客戶端
│       ├── prisma/
│       │   ├── schema.prisma     # ⭐ 資料模型定義
│       │   └── interfaces.ts     # 資料庫型別定義
│       ├── openapi.json          # API 規格
│       └── keys/                 # JWT RSA 金鑰
└── ...
```

### 開發模式：OpenAPI-First

```
1. 編輯 openapi.json 定義 API 規格
           ↓
2. just generate-schema 生成 TypeScript types + TypeBox schemas
           ↓
3. 實作業務邏輯
           ↓
4. Routes 使用 TypeBox 驗證請求
```

### 檔案命名規範

| 類型 | 命名格式 | 範例 |
|------|----------|------|
| Routes | `*-route.ts` | `contract-route.ts` |
| Services | `*-service.ts` | `contract-service.ts` |
| Repositories | `*-repository.ts` | `contract-repository.ts` |

## Prisma Schema

> 📖 完整清單請見：[ecs-ten-models.md](ecs-ten-models.md)

### Schema 配置

| 項目 | 值 |
|------|-----|
| 位置 | `packages/ecs-ten-server/prisma/schema.prisma` |
| 行數 | 4155 行 |
| 資料庫 | MS SQL Server |
| 功能 | multiSchema 預覽功能已啟用 |

### 四個 Schema 統計

| Schema | 模型數 | 用途 |
|--------|:------:|------|
| **join** | 60 | 關聯表（多對多） |
| **code** | 34 | 代碼表/參考資料 |
| **dbo** | 33 | 系統預設物件 |
| **data** | 31 | 業務資料表 |

### 核心 Model

| Schema | Model | 說明 |
|--------|-------|------|
| data | **Contract** | 合約主表 |
| data | **User** | 使用者 |
| data | **Department** | 部門 |
| data | **Partner** | 相對人 |
| code | **ExamStage** | 審查關卡 |
| code | **ContractType** | 合約類型 |
| join | **ContractExaminer** | 合約審查人 |
| join | **ContractAttachment** | 合約附件 |

### Contract 保留欄位（動態表單）

```
txt01-txt10, memo01-memo15, radio01-radio05,
checkBox01-checkBox05, select01-select05,
int01-int05, double01-double05, date01-date10
```

> ⚠️ 與 ecscore 的 Contract Entity 保留欄位結構一致

## Repository 層

### 位置

`packages/ecs-ten-server/src/repositories/`

### Contract 相關 Repository（18 個）

| Repository | 說明 |
|------------|------|
| contract-repository.ts | 核心合約 CRUD |
| contract-list-repository.ts | 合約列表查詢 |
| contract-attachment-repository.ts | 合約附件 |
| contract-examiner-repository.ts | 合約審查人 |
| contract-history-repository.ts | 合約歷程 |
| contract-partner-repository.ts | 合約相對人 |
| smart-contract-repository.ts | 智能合約操作 |

### 其他核心 Repository

| Repository | 說明 |
|------------|------|
| user-repository.ts | 使用者 |
| department-repository.ts | 部門 |
| partner-repository.ts | 相對人 |
| exam-stage-repository.ts | 審查關卡 |

## Service 層

### 位置

`packages/ecs-ten-server/src/services/`

### 統計

| 項目 | 數量 |
|------|------|
| Service 總數 | **52 個** |

### Contract 相關 Service

| Service | 說明 |
|---------|------|
| contract-service.ts | 核心合約業務 |
| contract-list-service.ts | 合約列表 |
| contract-history-service.ts | 合約歷程 |
| contract-attachment-service.ts | 合約附件 |
| contract-exam-stage-service.ts | 審查流程 |
| contract-signature-service.ts | 合約簽署 |

### 其他核心 Service

| Service | 說明 |
|---------|------|
| auth-service.ts | 認證（LDAP 整合） |
| permission-service.ts | 權限管理 |
| archive-service.ts | 檔案管理 |

## 認證機制

| 項目 | 說明 |
|------|------|
| JWT | RSA 金鑰對簽章（keys/private/, keys/public/） |
| Middleware | `authMiddleware`（可選）, `requireAuth`（必要） |
| LDAP | 透過 `auth-service.ts` 進行 Domain 登入 |

## 待研究項目

- [x] ~~Prisma Schema 完整分析~~ → 4155 行，158 個 Model
- [x] ~~4 個 schema 各包含什麼~~ → join(60), code(34), dbo(33), data(31)
- [x] ~~Repository 與 Service 的實作~~ → 18 個 Repository, 52 個 Service
- [x] ~~使用者權限過濾邏輯~~ → 見 [permission-control.md](permission-control.md)
- [x] ~~與 ecscore 的資料存取差異~~ → 見 [system-access-diff.md](system-access-diff.md)

---

## 更新記錄

| 日期 | 更新內容 |
|------|----------|
| 2026-01-21 | 建立文件框架 |
| 2026-01-21 | 從 CLAUDE.md 補充技術棧、架構圖、開發模式、認證機制 |
| 2026-01-21 | 完成 Prisma Schema 探索（158 個 Model），建立 ecs-ten-models.md |
