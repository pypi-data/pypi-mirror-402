# ECS MCP 開發案 - 技術文件

本目錄包含 ECS 合約管理系統 MCP Server 開發相關的技術文件。

## 文件結構

```
docs/
├── README.md                          # 本文件 - 文件索引
├── phase2/                            # 階段二：原始碼分析 ✅ 完成
│   ├── README.md                      # Phase 2 總覽與進度追蹤
│   ├── ecscore-analysis.md            # 後台管理系統分析
│   ├── ecscore-entities.md            # EF Core Entity 詳細清單
│   ├── ecs-ten-analysis.md            # 前台使用者系統分析
│   ├── ecs-ten-models.md              # Prisma Model 詳細清單
│   ├── db-schema.md                   # 資料庫 Schema（View/SP 清單）
│   ├── business-logic-contract.md     # 合約業務邏輯
│   ├── business-logic-approval.md     # 審核流程邏輯
│   ├── permission-control.md          # 權限控制機制
│   └── system-access-diff.md          # 兩套系統資料存取差異
├── phase3/                            # 階段三：MCP Server 開發 ✅ 完成
│   ├── README.md                      # Phase 3 總覽與進度追蹤
│   ├── development.md                 # 開發計劃與進度詳情
│   └── infrastructure.md              # 基礎設施實作
└── design/                            # 設計規格（穩定參考文件）
    ├── mcp-design.md                  # MCP 設計規格（Resources/Tool/Prompts）
    ├── mcp-views.md                   # View 欄位說明（37 個 View 詳細定義）
    ├── security.md                    # 安全機制（View 白名單、SQL 驗證、稽核）
    └── dss-scenarios.md               # DSS 決策支援情境分析
```

## 文件索引

### 階段二：原始碼分析 ✅ 完成

| 文件 | 說明 |
|------|------|
| [Phase 2 總覽](phase2/README.md) | 階段二工作項目與進度追蹤 |

#### 後台管理系統 (ecscore-master)
| 文件 | 說明 |
|------|------|
| [後台系統分析](phase2/ecscore-analysis.md) | ecscore-master 原始碼分析 |
| [Entity 清單](phase2/ecscore-entities.md) | EF Core 104 個 Entity 詳細清單 |

#### 前台使用者系統 (ecs-ten-main)
| 文件 | 說明 |
|------|------|
| [前台系統分析](phase2/ecs-ten-analysis.md) | ecs-ten-main 原始碼分析 |
| [Model 清單](phase2/ecs-ten-models.md) | Prisma 158 個 Model 詳細清單 |

#### 資料庫與業務邏輯
| 文件 | 說明 |
|------|------|
| [DB Schema](phase2/db-schema.md) | 資料庫結構、View/SP 清單 |
| [合約業務邏輯](phase2/business-logic-contract.md) | 合約生命週期管理 |
| [審核流程邏輯](phase2/business-logic-approval.md) | 審核簽核流程 |
| [權限控制機制](phase2/permission-control.md) | 三層授權與角色機制 |
| [系統存取差異](phase2/system-access-diff.md) | 兩套系統資料存取比較 |

### 階段三：MCP Server 開發 ✅ 完成

| 文件 | 說明 |
|------|------|
| [Phase 3 總覽](phase3/README.md) | 階段三工作項目與進度追蹤 |
| [開發計劃](phase3/development.md) | 概覽、設計理念、開發階段 |
| [基礎設施](phase3/infrastructure.md) | 連線池、日誌、錯誤處理實作 |

### 設計規格

| 文件 | 說明 |
|------|------|
| [MCP 設計規格](design/mcp-design.md) | Resources、Tool、Prompts 設計 |
| [View 欄位說明](design/mcp-views.md) | 37 個可查詢 View 的完整欄位定義 |
| [安全機制](design/security.md) | View 白名單、SQL 驗證、稽核日誌 |
| [DSS 決策情境](design/dss-scenarios.md) | 各部門使用情境與可行性分析 |

## 文件維護原則

1. **單一資訊來源** - 同一資訊只存在一處，其他地方以連結引用
2. **按階段分類** - phase2/、phase3/ 為開發工作文件
3. **設計規格獨立** - design/ 存放穩定的設計參考文件
4. **進度追蹤** - 各階段 README.md 負責追蹤該階段進度

## 相關文件

- [CLAUDE.md](../CLAUDE.md) - 專案總覽與開發日誌
- [MSSQL Connection Infomation.md](../MSSQL%20Connection%20Infomation.md) - 資料庫連線資訊
