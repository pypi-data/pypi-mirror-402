# Phase 2：原始碼分析與 DB Schema 理解

## 目標

透過分析 ECS 系統的原始碼，完整理解資料庫架構與業務邏輯，為開發 MCP Server 提供參考依據。

## 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    SQL Server 資料庫                     │
│          （187 張表 / 70 Views / 504 SPs）               │
└─────────────────────────────────────────────────────────┘
          ▲                              ▲
          │                              │
┌─────────┴─────────┐      ┌─────────────┴─────────────┐
│  ecscore-master   │      │      ecs-ten-main         │
│  ─────────────    │      │    ─────────────────      │
│  後台管理系統      │      │    前台使用者系統          │
│  管理者權限        │      │    一般使用者權限          │
│  ─────────────    │      │    ─────────────────      │
│  ASP.NET Core 8   │      │    Express + Bun          │
│  EF Core 8        │      │    Prisma ORM             │
│  Vue 3 前端       │      │    TypeScript             │
└───────────────────┘      └───────────────────────────┘
```

> **MCP Server 定位**：直接存取資料庫，需從兩套系統理解完整的資料庫邏輯與權限控制。

## 工作項目

> **分析順序說明**：程式碼是資料結構的定義來源，資料庫 Schema 是其結果。
> 因此採用「程式碼優先」策略，從兩套系統的 ORM 層開始，資料庫作為驗證對照。

### 1. ecscore-master 分析（後台管理系統）
- [x] 專案結構概覽（從 CLAUDE.md 取得）
- [x] **Entity 模型分析** - 104 個 Entity
- [x] **DbContext 分析** - EcsDbContext（新）+ EcsDataContext（舊）
- [x] Repository 層分析
- [x] 核心業務邏輯（合約、審核流程）
- [x] 權限控制機制

### 2. ecs-ten-main 分析（前台使用者系統）
- [x] 專案結構概覽（從 CLAUDE.md 取得）
- [x] **Prisma Schema 分析** - 158 個 Model，4 個 schema
- [x] Repository 層分析 - 18 個 Repository
- [x] Service 層業務邏輯 - 52 個 Service
- [x] 使用者權限過濾邏輯

### 3. 資料庫驗證 - 對照兩套系統
- [x] 匯出完整資料表清單（187 張表）
- [x] 對照 EF Core Entity 驗證欄位（95%+ 覆蓋率）
- [x] 對照 Prisma Schema 驗證欄位（82% 覆蓋率）
- [x] 識別兩套系統的資料存取差異
- [x] 記錄 View（70 個）和 Stored Procedure（504 個）

## 分析文件

| 順序 | 文件 | 說明 | 狀態 |
|:----:|------|------|------|
| 1 | [ecscore-analysis.md](ecscore-analysis.md) | 後台管理系統分析 | ✅ 完成 |
| 1.1 | [ecscore-entities.md](ecscore-entities.md) | EF Core Entity 詳細清單 | ✅ 完成 |
| 2 | [ecs-ten-analysis.md](ecs-ten-analysis.md) | 前台使用者系統分析 | ✅ 完成 |
| 2.1 | [ecs-ten-models.md](ecs-ten-models.md) | Prisma Model 詳細清單 | ✅ 完成 |
| 3 | [db-schema.md](db-schema.md) | 資料庫 Schema（View/SP 清單） | ✅ 完成 |
| 4 | [business-logic-contract.md](business-logic-contract.md) | 合約業務邏輯 | ✅ 完成 |
| 5 | [business-logic-approval.md](business-logic-approval.md) | 審核流程邏輯 | ✅ 完成 |
| 6 | [permission-control.md](permission-control.md) | 權限控制機制 | ✅ 完成 |
| 7 | [system-access-diff.md](system-access-diff.md) | 兩套系統資料存取差異 | ✅ 完成 |

## 進度追蹤

### 2026-01-21（Phase 2 完成）
- 建立文件結構
- 調整分析順序：採用「程式碼優先」策略
- 釐清雙系統架構：ecscore-master（後台）+ ecs-ten-main（前台）
- 從 CLAUDE.md 取得兩套系統的技術棧與架構概覽
- 調整文件結構：按系統分類而非前後端分類
- 完成 ecscore Entity 模型探索（104 個 Entity）
- 完成 ecs-ten Prisma Schema 探索（158 個 Model）
- 建立詳細清單文件：ecscore-entities.md, ecs-ten-models.md
- **完成核心業務邏輯分析**：合約生命週期、審核流程
- **完成權限控制機制分析**：三層授權、角色機制
- **完成資料庫驗證對照**：EF Core 95%+、Prisma 82% 覆蓋率
- **完成 View/SP 記錄**：70 Views、504 Stored Procedures
- **完成兩套系統資料存取差異分析**

---

## 參考資源

| 系統 | 原始碼位置 | CLAUDE.md |
|------|-----------|-----------|
| 後台管理 | `reference/ecscore-master/` | `reference/ecscore-master/CLAUDE.md` |
| 前台使用者 | `reference/ecs-ten-main/` | `reference/ecs-ten-main/CLAUDE.md` |
| 前台服務層 | `reference/ecs-ten-main/packages/ecs-ten-server/` | 同目錄下有 CLAUDE.md |

- 資料庫連線：參見 [MSSQL Connection Infomation.md](../../MSSQL%20Connection%20Infomation.md)
