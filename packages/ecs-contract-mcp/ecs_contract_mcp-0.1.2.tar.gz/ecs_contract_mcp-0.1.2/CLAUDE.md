# ECS 合約管理系統 MCP 開發案

## 專案概述

本專案目標是為 ECS 合約管理系統開發 MCP (Model Context Protocol) Server，以便透過 AI 工具與系統資料庫進行互動。

## 專案結構

```
ECS/
├── CLAUDE.md                              # 本文件 - 專案總覽
├── MSSQL Connection Infomation.md         # 資料庫連線資訊
├── docs/                                  # 技術文件
│   ├── README.md                          # 文件索引
│   ├── phase2/                            # 階段二：原始碼分析 ✅ 完成
│   │   ├── README.md                      # Phase 2 進度追蹤
│   │   ├── ecscore-analysis.md            # 後台系統分析
│   │   ├── ecscore-entities.md            # EF Core Entity 清單
│   │   ├── ecs-ten-analysis.md            # 前台系統分析
│   │   ├── ecs-ten-models.md              # Prisma Model 清單
│   │   ├── db-schema.md                   # 資料庫 Schema
│   │   ├── business-logic-contract.md     # 合約業務邏輯
│   │   ├── business-logic-approval.md     # 審核流程邏輯
│   │   ├── permission-control.md          # 權限控制機制
│   │   └── system-access-diff.md          # 兩套系統存取差異
│   ├── phase3/                            # 階段三：MCP Server 開發 ✅ 完成
│   │   ├── README.md                      # Phase 3 進度追蹤
│   │   ├── development.md                 # 開發計劃與進度詳情
│   │   └── infrastructure.md              # 基礎設施實作
│   └── design/                            # 設計規格（穩定參考文件）
│       ├── mcp-design.md                  # MCP 設計規格（Resources/Tool/Prompts）
│       ├── mcp-views.md                   # View 欄位說明（37 個 View 完整定義）
│       ├── security.md                    # 安全機制（View 白名單、SQL 驗證、稽核）
│       └── dss-scenarios.md               # DSS 決策支援情境分析
├── mcp_server/                            # MCP Server 程式碼
└── reference/                             # 參考原始碼
    ├── ecscore-master/                    # 系統後端原始碼
    └── ecs-ten-main/                      # 系統前端原始碼
```

## 開發計劃

### 階段一：MSSQL 資料庫連線測通 ✅ 完成
- [x] 確認資料庫連線資訊
- [x] 安裝 MSSQL 客戶端工具 (msodbcsql18, mssql-tools18)
- [x] 測試連線是否正常
- [x] 驗證存取權限

### 階段二：分析原始碼了解 DB Schema 架構邏輯 ✅ 完成

> 詳細分析文件：[docs/phase2/README.md](docs/phase2/README.md)

**分析成果：**
- 完成後台系統 (ecscore-master) 分析：104 個 EF Core Entity
- 完成前台系統 (ecs-ten-main) 分析：158 個 Prisma Model
- 完成資料庫驗證：187 張表、70 Views、504 Stored Procedures
- 完成核心業務邏輯分析：合約生命週期、審核流程、權限控制

### 階段三：開發 ECS MCP Server ✅ 完成

> 詳細開發計劃：[docs/phase3/development.md](docs/phase3/development.md)
> MCP 設計規格：[docs/design/mcp-design.md](docs/design/mcp-design.md)
> DSS 情境分析：[docs/design/dss-scenarios.md](docs/design/dss-scenarios.md)

**設計理念：能力驅動架構**

不是預先定義固定情境的 Tools，而是：
- **Resource**：提供豐富的背景知識（Schema、業務邏輯、對照表）
- **Tool**：提供安全的 SQL 查詢能力（唯一的 `query_database` Tool）
- **Prompt**：提供分析框架指引

讓 AI 像資料分析師一樣，能夠根據任意問題組合查詢、匯總答案。

**技術決策：**
- 開發語言：Python 3.11+
- 部署方式：獨立服務（stdio transport）
- 目標工具：Claude Desktop
- 安全機制：View 白名單 + Row-Level Security + 稽核日誌

**子階段：**

#### Phase 3.1：核心基礎建設 ✅ 完成
- [x] 初始化 Python 專案結構
- [x] 實作資料庫連線池
- [x] 實作安全查詢執行器（View 白名單、SQL 驗證）
- [x] 實作 MCP Server 框架
- [x] 實作稽核記錄

#### Phase 3.2：Resources 實作 ✅ 完成
- [x] Schema Resources（overview、views、relationships）
- [x] Context Resources（business-terms、contract-lifecycle、approval-flow、sla-definitions）
- [x] Reference Resources（contract-types、departments、exam-stages、currencies）
- [x] Stats Resources（dashboard）

#### Phase 3.3：Tool 與 Prompt 實作 ✅ 完成
- [x] `query_database` Tool（核心查詢工具）
- [x] `data_analysis_guide` Prompt（分析框架指引）
- [x] `common_queries` Prompt（常見查詢範例）

#### Phase 3.4：安全強化與測試 ✅ 完成
- [x] View 白名單機制驗證（26 個測試）
- [x] SQL Injection 防護測試（42 個測試）
- [x] 稽核日誌完整性測試（15 個測試）
- [x] 錯誤處理測試（15 個測試）
- [x] 端對端測試腳本

## 開發日誌

### 2026-01-21: 專案啟動
- 建立專案目錄結構
- 確認參考資料位置
- 制定三階段開發計劃

### 2026-01-21: 階段一完成 - MSSQL 資料庫連線測通
- 透過 Homebrew 安裝 Microsoft ODBC Driver 18 和 mssql-tools18
- 發現原始連線資訊文件中的帳號密碼不正確
- 從原始碼 appsettings 中找到正確的連線資訊
- 成功連線到 SQL Server 2019 Enterprise Edition
- 資料庫共有 168 個資料表

### 2026-01-21: 階段二完成 - 原始碼分析與 DB Schema 理解
- 採用「程式碼優先」分析策略
- 完成 ecscore-master 後台系統分析（ASP.NET Core 8 + EF Core 8）
- 完成 ecs-ten-main 前台系統分析（Express + Bun + Prisma）
- 驗證資料庫結構：EF Core 95%+ 覆蓋率、Prisma 82% 覆蓋率
- 完成核心業務邏輯文件：合約、審核、權限控制
- 建立完整的技術文件共 9 份

### 2026-01-21: 階段三啟動 - MCP Server 開發計劃制定
- 完成 DSS 決策支援情境分析（docs/dss2.md）
- 確定技術選型：Python 3.11+ / 獨立服務 / Claude Desktop
- 初版規劃 14 個固定情境 MCP Tools

### 2026-01-21: 架構重新設計 - 從情境驅動到能力驅動
- 發現問題：固定情境 Tools 無法回答開放式分析問題
- 重新設計：採用「能力驅動」架構
  - **Resource**：豐富的背景知識（12 個 Resources）
    - Schema：overview、views、relationships
    - Context：business-terms、contract-lifecycle、approval-flow、sla-definitions
    - Reference：contract-types、departments、exam-stages、currencies（動態）
    - Stats：dashboard（動態）
  - **Tool**：精簡的查詢能力（1 個 Tool）
    - `query_database`：安全的 SQL 查詢，View 白名單限制
  - **Prompt**：分析框架指引（2 個 Prompts）
    - `data_analysis_guide`：分析步驟框架
    - `common_queries`：常見查詢範例
- 核心思想：讓 AI 成為「資料分析師」，而非「固定報表產生器」
- 更新文件：dev.md、dev-mcp-design.md

### 2026-01-21: Phase 3.1 完成 - 核心基礎建設
- 建立 MCP Server 專案結構（mcp_server/）
- 實作核心模組：
  - `config.py`：環境變數配置（pydantic-settings）
  - `utils/logging.py`：日誌系統（structlog）
  - `utils/errors.py`：錯誤代碼與例外類別
  - `utils/audit.py`：稽核日誌
  - `database/connection.py`：資料庫連線池（pyodbc + asyncio）
  - `database/allowed_views.py`：View 白名單（37 個 Views）
  - `database/query_executor.py`：安全查詢執行器
  - `server.py`：MCP Server 入口（FastMCP）
- 安全機制驗證：
  - SQL Injection 防護（只允許 SELECT、禁止危險關鍵字）
  - View 白名單驗證（支援 `[view].[Table]` 格式）
  - 自動 TOP 限制（預設 1000 筆）
- 建立驗證腳本：`scripts/verify_setup.py`
- 所有測試通過，MCP Server 可正常啟動

### 2026-01-21: Phase 3.2 完成 - Resources 實作
- 實作 12 個 MCP Resources：
  - **Schema Resources**（靜態）：
    - `ecs://schema/overview`：資料庫概覽
    - `ecs://schema/views`：View 清單與欄位說明
    - `ecs://schema/relationships`：資料表關聯
  - **Context Resources**（靜態）：
    - `ecs://context/business-terms`：業務術語定義
    - `ecs://context/contract-lifecycle`：合約生命週期
    - `ecs://context/approval-flow`：審核流程說明
    - `ecs://context/sla-definitions`：SLA 定義
  - **Reference Resources**（動態，從資料庫取得）：
    - `ecs://reference/contract-types`：合約類型
    - `ecs://reference/departments`：部門清單
    - `ecs://reference/exam-stages`：審核階段
    - `ecs://reference/currencies`：幣別清單
  - **Stats Resources**（動態）：
    - `ecs://stats/dashboard`：系統即時統計
- 撰寫 39 個單元測試，全部通過
- 動態 Resources 實作錯誤處理，在資料庫連線失敗時優雅降級

### 2026-01-21: Phase 3.3 完成 - Tool 與 Prompt 實作
- 實作核心查詢工具 `query_database`：
  - 位置：`mcp_server/tools/query.py`
  - 完整的資料類型序列化（datetime、Decimal、bytes 等）
  - 整合安全查詢執行器（View 白名單、SQL 驗證）
  - 統一的回傳格式（success、columns、rows、row_count、truncated、message）
  - 完善的錯誤處理（SecurityError、DatabaseError）
- 實作兩個分析指引 Prompts：
  - `data_analysis_guide`：資料分析五步驟框架
  - `common_queries`：10+ 個常見查詢 SQL 範例
- 更新 `server.py` 註冊 Tools 和 Prompts
- 撰寫 21 個單元測試（Tools 13 個、Prompts 8 個），全部通過
- MCP Server 完整功能驗證：
  - **Tools**: query_database, health_check（共 2 個）
  - **Prompts**: data_analysis_guide, common_queries（共 2 個）
  - **Resources**: 12 個（靜態 7 個、動態 5 個）

### 2026-01-21: Phase 3.4 完成 - 安全強化與測試
- 建立完整的安全測試套件（tests/test_security/）：
  - **View 白名單測試**（test_whitelist.py）：26 個測試
    - 名稱正規化（括號格式、混合格式）
    - 白名單檢查（允許/禁止的 View）
    - SQL 表格提取（FROM、JOIN、子查詢）
    - 白名單完整性驗證
  - **SQL Injection 防護測試**（test_sql_injection.py）：42 個測試
    - SELECT 限制（INSERT/UPDATE/DELETE/DROP 等阻擋）
    - 危險關鍵字檢測（EXEC/GRANT/BACKUP 等）
    - SQL 註解阻擋（-- 和 /* */）
    - UNION 注入、堆疊查詢防護
    - 經典注入向量測試
    - Row limit 強制執行
  - **稽核日誌測試**（test_audit.py）：15 個測試
    - 查詢記錄完整性
    - 安全違規記錄
    - 日誌欄位驗證
    - 日誌層級正確性
  - **錯誤處理測試**（test_error_handling.py）：15 個測試
    - 各類錯誤類型驗證
    - 錯誤恢復測試
    - 優雅降級處理
    - 錯誤回應格式（中文訊息）
- 建立端對端測試腳本（scripts/e2e_test.py）：
  - 配置載入驗證
  - 白名單機制驗證
  - SQL 驗證機制驗證
  - 資料庫連線測試
  - MCP Server 初始化測試
- 測試統計：98 個測試，100% 通過率

---

## 快速參考

### Phase 3 開發文件
| 資源 | 位置 |
|------|------|
| **Phase 3 總覽** | [docs/phase3/README.md](docs/phase3/README.md) |
| **開發計劃** | [docs/phase3/development.md](docs/phase3/development.md) |
| **基礎設施** | [docs/phase3/infrastructure.md](docs/phase3/infrastructure.md) |

### 設計規格
| 資源 | 位置 |
|------|------|
| **MCP 設計規格** | [docs/design/mcp-design.md](docs/design/mcp-design.md) |
| **View 欄位說明** | [docs/design/mcp-views.md](docs/design/mcp-views.md) |
| **安全機制** | [docs/design/security.md](docs/design/security.md) |
| DSS 決策支援情境 | [docs/design/dss-scenarios.md](docs/design/dss-scenarios.md) |

### Phase 2 分析文件
| 資源 | 位置 |
|------|------|
| Phase 2 總覽 | [docs/phase2/README.md](docs/phase2/README.md) |
| DB Schema | [docs/phase2/db-schema.md](docs/phase2/db-schema.md) |
| 後台系統分析 | [docs/phase2/ecscore-analysis.md](docs/phase2/ecscore-analysis.md) |
| 前台系統分析 | [docs/phase2/ecs-ten-analysis.md](docs/phase2/ecs-ten-analysis.md) |
| 合約業務邏輯 | [docs/phase2/business-logic-contract.md](docs/phase2/business-logic-contract.md) |
| 權限控制機制 | [docs/phase2/permission-control.md](docs/phase2/permission-control.md) |

### 其他
| 資源 | 位置 |
|------|------|
| 資料庫連線資訊 | [MSSQL Connection Infomation.md](MSSQL%20Connection%20Infomation.md) |
| 文件索引 | [docs/README.md](docs/README.md) |

## 文件維護原則

1. **單一資訊來源** - 同一資訊只存在一處，其他地方以連結引用
2. **按系統分類** - 後台/前台系統分析各自獨立文件
3. **DB Schema 共用** - 資料庫結構為共用參考
4. **本文件職責** - 專案總覽、開發日誌、快速參考
