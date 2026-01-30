# Phase 3：MCP Server 開發

## 目標

開發 ECS 合約管理系統的 MCP (Model Context Protocol) Server，讓 AI 工具能夠安全地查詢系統資料庫，協助資料分析與決策支援。

## 設計理念

```
┌─────────────────────────────────────────────────────────────┐
│                        MCP Server                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Resources  │  │    Tool     │  │       Prompts       │ │
│  │  ─────────  │  │  ─────────  │  │  ─────────────────  │ │
│  │  背景知識    │  │  查詢能力   │  │     分析框架指引    │ │
│  │  (12 個)    │  │ (1 個)      │  │     (2 個)          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               SQL Server 資料庫（唯讀存取）                   │
│                   37 個白名單 Views                          │
└─────────────────────────────────────────────────────────────┘
```

**能力驅動架構**：不是預先定義固定情境的 Tools，而是讓 AI 成為「資料分析師」，自行組合查詢回答任意問題。

## 技術規格

| 項目 | 選型 |
|------|------|
| 開發語言 | Python 3.11+ |
| MCP SDK | mcp >= 1.0.0 |
| 資料庫驅動 | pyodbc + asyncio |
| 部署方式 | 獨立服務（stdio transport） |
| 目標工具 | Claude Desktop |

## 開發階段

### Phase 3.1：核心基礎建設 ✅ 完成
- [x] Python 專案結構
- [x] 資料庫連線池
- [x] 安全查詢執行器（View 白名單、SQL 驗證）
- [x] MCP Server 框架
- [x] 稽核日誌

### Phase 3.2：Resources 實作 ✅ 完成
- [x] Schema Resources（overview、views、relationships）
- [x] Context Resources（business-terms、contract-lifecycle、approval-flow、sla-definitions）
- [x] Reference Resources（contract-types、departments、exam-stages、currencies）
- [x] Stats Resources（dashboard）

### Phase 3.3：Tool 與 Prompt 實作 ✅ 完成
- [x] `query_database` Tool（核心查詢工具）
- [x] `data_analysis_guide` Prompt
- [x] `common_queries` Prompt

### Phase 3.4：安全強化與測試 ✅ 完成
- [x] View 白名單測試（26 個）
- [x] SQL Injection 防護測試（42 個）
- [x] 稽核日誌測試（15 個）
- [x] 錯誤處理測試（15 個）
- [x] 端對端測試腳本

## 文件索引

| 文件 | 說明 |
|------|------|
| [development.md](development.md) | 開發計劃與進度詳情 |
| [infrastructure.md](infrastructure.md) | 基礎設施實作（連線池、日誌、錯誤處理） |

> **設計規格**請見 [docs/design/](../design/) 目錄

## 測試統計

| 測試類型 | 測試數量 | 通過率 |
|----------|----------|--------|
| View 白名單 | 26 | 100% |
| SQL Injection | 42 | 100% |
| 稽核日誌 | 15 | 100% |
| 錯誤處理 | 15 | 100% |
| **總計** | **98** | **100%** |

## 相關資源

- 設計規格：[docs/design/](../design/)
- Phase 2 分析：[docs/phase2/](../phase2/)
- MCP Server 程式碼：[mcp_server/](../../mcp_server/)
- 測試程式碼：[tests/](../../tests/)
