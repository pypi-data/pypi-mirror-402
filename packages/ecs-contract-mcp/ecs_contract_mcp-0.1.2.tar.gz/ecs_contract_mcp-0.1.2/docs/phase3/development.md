# ECS MCP Server 開發計劃

> Phase 3：開發 ECS MCP Server

## 設計理念

### 從「情境驅動」到「能力驅動」

| 設計方式 | 說明 | 問題 |
|---------|------|------|
| ~~情境驅動~~ | 預先定義 N 個情境，設計 N 個 Tools | 第 N+1 個情境就無法處理 |
| **能力驅動** | 給 AI 足夠的知識和查詢能力 | AI 自己組合出任意問題的答案 |

**核心思想**：MCP Server 不是「固定報表產生器」，而是讓 AI 成為「資料分析師」。

### AI 工作流程

```
用戶提問
    ↓
讀取 Resource（Schema、業務邏輯、術語定義）
    ↓
理解問題需要什麼資料
    ↓
規劃查詢步驟（可能需要多個 SQL）
    ↓
執行 SQL，取得結果
    ↓
分析、匯總、回答
```

### MCP 三大功能分工

| 功能 | 職責 | 數量 |
|------|------|------|
| **Resource** | 提供背景知識（Schema、業務邏輯、對照表） | 豐富 |
| **Tool** | 提供安全的查詢能力 | 精簡 |
| **Prompt** | 提供分析框架指引 | 精簡 |

---

## 技術決策

| 項目 | 決策 | 說明 |
|------|------|------|
| 開發語言 | Python 3.11+ | MCP SDK 生態系成熟，資料處理能力強 |
| MCP SDK | `mcp>=1.0.0,<2.0.0` | Anthropic 官方維護 |
| 資料庫驅動 | `pyodbc` + `asyncio.to_thread()` | 最成熟穩定的 MSSQL 驅動，透過線程池支援 async |
| 部署方式 | 獨立服務 | stdio transport for Claude Desktop |
| 目標工具 | Claude Desktop | 透過 claude_desktop_config.json 配置 |
| 認證模式 | 單一系統帳號 | 不實作多用戶 RLS，使用唯讀帳號 |
| 稽核方式 | 日誌檔案 | 不新增資料庫表，僅寫入日誌 |

**SDK 參考資源**：
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25)

---

## 專案結構

```
ECS/
├── mcp_server/                    # MCP Server 主目錄
│   ├── __init__.py
│   ├── __main__.py                # 模組入口（python -m mcp_server）
│   ├── server.py                  # MCP Server 入口
│   ├── config.py                  # 配置管理（環境變數）
│   │
│   ├── content/                   # 靜態 Resource 內容
│   │   ├── schema_overview.md     # 資料庫概覽
│   │   ├── schema_views.md        # View 說明
│   │   ├── business_terms.md      # 業務術語
│   │   └── ...
│   │
│   ├── database/                  # 資料庫層
│   │   ├── __init__.py
│   │   ├── connection.py          # 連線池管理
│   │   └── query_executor.py      # 安全查詢執行器
│   │
│   ├── tools/                     # MCP Tools
│   │   ├── __init__.py
│   │   └── query.py               # 核心查詢 Tool
│   │
│   ├── resources/                 # MCP Resources
│   │   ├── __init__.py
│   │   ├── schema.py              # Schema 相關 Resources
│   │   ├── context.py             # 業務脈絡 Resources
│   │   └── reference.py           # 對照表 Resources（動態）
│   │
│   ├── prompts/                   # MCP Prompts
│   │   ├── __init__.py
│   │   └── analysis_guide.py      # 分析框架指引
│   │
│   └── utils/                     # 工具函數
│       ├── __init__.py
│       ├── audit.py               # 稽核記錄
│       ├── errors.py              # 錯誤處理
│       └── logging.py             # 日誌配置
│
├── tests/                         # 測試
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_tools/
│   ├── test_resources/
│   └── test_security/
│
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 文件索引

| 文件 | 內容 |
|------|------|
| **本文件** | 概覽、設計理念、開發階段 |
| [infrastructure.md](infrastructure.md) | 基礎設施（連線池、錯誤處理、日誌） |
| [mcp-design.md](../design/mcp-design.md) | MCP 設計（Resources、Tool、Prompts） |
| [mcp-views.md](../design/mcp-views.md) | View 欄位說明（37 個 View 完整定義） |
| [security.md](../design/security.md) | 安全機制（View 白名單、SQL 驗證、稽核日誌） |
| [dss-scenarios.md](../design/dss-scenarios.md) | DSS 決策支援情境分析 |

---

## 開發階段

### Phase 3.1：核心基礎建設 ✅ 完成

**目標**：建立 MCP Server 骨架與安全查詢機制

#### 工作項目

- [x] 初始化 Python 專案結構
- [x] 設定 pyproject.toml 與依賴
- [x] 實作環境變數配置 (`config.py`)
- [x] 實作日誌系統 (`utils/logging.py`)
- [x] 實作錯誤處理 (`utils/errors.py`)
- [x] 實作資料庫連線池 (`database/connection.py`)
- [x] 實作 View 白名單 (`database/allowed_views.py`)
- [x] 實作安全查詢執行器 (`database/query_executor.py`)
- [x] 實作稽核日誌 (`utils/audit.py`)
- [x] 實作基本 MCP Server 框架 (`server.py`)
- [x] 撰寫 Claude Desktop 配置說明

#### 技術細節

**MCP Server 入口**：

```python
# server.py
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP

from mcp_server.database.connection import DatabasePool
from mcp_server.utils.logging import setup_logging, logger

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """應用程式生命週期管理"""
    setup_logging()
    logger.info("mcp_server_starting")
    await DatabasePool.init()
    try:
        yield
    finally:
        await DatabasePool.close()
        logger.info("mcp_server_stopped")

mcp = FastMCP(
    name="ecs-contract-mcp",
    lifespan=app_lifespan
)

# 註冊 Resources, Tools, Prompts
from mcp_server.resources import register_resources
from mcp_server.tools import register_tools
from mcp_server.prompts import register_prompts

register_resources(mcp)
register_tools(mcp)
register_prompts(mcp)

if __name__ == "__main__":
    mcp.run()
```

**Claude Desktop 配置**：

```json
{
  "mcpServers": {
    "ecs-contract": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/ECS",
      "env": {
        "DB_SERVER": "your-server",
        "DB_NAME": "LT_ECS_LTCCore",
        "DB_USER": "readonly_user",
        "DB_PASSWORD": "your_password",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**認證模式**：單一系統帳號（readonly_user），不實作多用戶 Row-Level Security。

---

### Phase 3.2：Resources 實作 ✅ 完成

**目標**：提供 AI 所需的背景知識

#### Resource 清單

| URI | 類型 | 說明 |
|-----|------|------|
| `ecs://schema/overview` | 靜態 | 資料庫概覽 |
| `ecs://schema/views` | 靜態 | View 清單與欄位說明 |
| `ecs://schema/relationships` | 靜態 | 資料表關聯 |
| `ecs://context/business-terms` | 靜態 | 業務術語定義 |
| `ecs://context/contract-lifecycle` | 靜態 | 合約生命週期 |
| `ecs://context/approval-flow` | 靜態 | 審核流程說明 |
| `ecs://context/sla-definitions` | 靜態 | SLA 定義 |
| `ecs://reference/contract-types` | 動態 | 合約類型清單 |
| `ecs://reference/departments` | 動態 | 部門清單 |
| `ecs://reference/exam-stages` | 動態 | 審核階段清單 |
| `ecs://reference/currencies` | 動態 | 幣別清單 |
| `ecs://stats/dashboard` | 動態 | 系統即時統計 |

> 詳細規格見 [mcp-design.md](../design/mcp-design.md)
> View 欄位說明見 [mcp-views.md](../design/mcp-views.md)

#### 工作項目

- [x] 實作 `resources/schema.py`
  - [x] `ecs://schema/overview` - 資料庫概覽
  - [x] `ecs://schema/views` - View 清單（引用靜態內容）
  - [x] `ecs://schema/relationships` - 資料表關聯圖
- [x] 實作 `resources/context.py`
  - [x] `ecs://context/business-terms` - 業務術語定義
  - [x] `ecs://context/contract-lifecycle` - 合約生命週期
  - [x] `ecs://context/approval-flow` - 審核流程說明
  - [x] `ecs://context/sla-definitions` - SLA 定義
- [x] 實作 `resources/reference.py`（動態，從資料庫取得）
  - [x] `ecs://reference/contract-types` - 合約類型
  - [x] `ecs://reference/departments` - 部門清單
  - [x] `ecs://reference/exam-stages` - 審核階段
  - [x] `ecs://reference/currencies` - 幣別清單
- [x] 實作 `resources/stats.py`（動態）
  - [x] `ecs://stats/dashboard` - 系統即時統計
- [x] 撰寫 Resource 單元測試

---

### Phase 3.3：Tool 與 Prompt 實作 ✅ 完成

**目標**：提供安全的查詢能力與分析指引

#### Tool 清單

| Tool | 說明 |
|------|------|
| `query_database` | 核心查詢工具（唯一的 Tool） |

#### Prompt 清單

| Prompt | 說明 |
|--------|------|
| `data_analysis_guide` | 資料分析框架指引 |
| `common_queries` | 常見查詢範例 |

> 詳細規格見 [mcp-design.md](../design/mcp-design.md)

#### 工作項目

- [x] 實作 `tools/query.py`
  - [x] `query_database` Tool 主體
  - [x] 輸入驗證（sql、purpose 參數）
  - [x] 回傳格式（columns、rows、metadata）
  - [x] 錯誤處理（SecurityError、QueryError）
- [x] 實作 `prompts/analysis_guide.py`
  - [x] `data_analysis_guide` - 分析步驟框架
  - [x] `common_queries` - 常見查詢範例
- [x] 撰寫 Tool 單元測試
  - [x] 正常查詢測試
  - [x] 安全限制測試（非 SELECT、非白名單 View）
  - [x] 結果截斷測試（超過 1000 筆）
  - [x] 錯誤處理測試
- [x] 撰寫 Prompt 測試

---

### Phase 3.4：安全強化與測試 ✅ 完成

**目標**：確保安全性與穩定性

#### 工作項目

- [x] View 白名單機制驗證
  - 測試檔案：`tests/test_security/test_whitelist.py`
  - 26 個測試案例涵蓋：名稱正規化、白名單檢查、SQL 提取、表格驗證
- [x] SQL Injection 防護測試
  - 測試檔案：`tests/test_security/test_sql_injection.py`
  - 42 個測試案例涵蓋：SELECT 限制、危險關鍵字、註解阻擋、UNION 注入、堆疊查詢、編碼繞過
- [x] 稽核日誌完整性測試
  - 測試檔案：`tests/test_security/test_audit.py`
  - 15 個測試案例涵蓋：查詢記錄、安全違規記錄、日誌欄位完整性、日誌層級
- [x] 錯誤處理與回復測試
  - 測試檔案：`tests/test_security/test_error_handling.py`
  - 15 個測試案例涵蓋：錯誤類型、錯誤恢復、優雅降級、錯誤回應格式
- [x] 端對端測試腳本
  - 測試腳本：`scripts/e2e_test.py`
  - 涵蓋：配置載入、白名單、SQL 驗證、資料庫連線、MCP Server 初始化

#### 測試統計

| 測試類型 | 測試數量 | 通過率 |
|----------|----------|--------|
| View 白名單 | 26 | 100% |
| SQL Injection | 42 | 100% |
| 稽核日誌 | 15 | 100% |
| 錯誤處理 | 15 | 100% |
| **總計** | **98** | **100%** |

---

## 測試策略

### 單元測試
- SQL 語法驗證邏輯
- View 白名單檢查
- 權限過濾注入
- 稽核記錄格式

### 整合測試
- 資料庫連線與查詢
- MCP Protocol 交互
- Resource 內容正確性

### 安全測試
- SQL Injection 攻擊向量
- 未授權 Table 存取嘗試
- 權限繞過嘗試

### 端對端測試
- Claude Desktop 實際使用情境
- 複雜查詢組合
- 錯誤情況處理

---

## 驗收標準

### Phase 3.1 驗收 ✅
- [x] MCP Server 可啟動且無錯誤
- [ ] Claude Desktop 可連線到 MCP Server（待實際測試）
- [x] 資料庫連線池正常運作
- [x] 日誌正確輸出
- [x] 環境變數正確讀取

### Phase 3.2 驗收 ✅
- [x] 所有 Resource 可正常讀取
- [x] 靜態 Resource 內容完整正確
- [x] 動態 Resource 從資料庫正確取得
- [ ] AI 可根據 Resource 理解系統（待實際測試）

### Phase 3.3 驗收 ✅
- [x] `query_database` Tool 正常運作
- [x] 只允許 SELECT 語句
- [x] 只允許查詢白名單 View
- [x] 回傳筆數正確限制
- [x] 稽核日誌正確記錄
- [ ] AI 可組合查詢回答任意分析問題（待 Phase 3.4 端對端測試驗證）

### Phase 3.4 驗收 ✅
- [x] 所有安全測試通過（98 個測試，100% 通過率）
- [x] 錯誤處理完善
- [ ] Claude Desktop 端對端測試（待實際使用驗證）

---

## 相關文件

| 文件 | 說明 |
|------|------|
| [DSS 決策支援情境](../design/dss-scenarios.md) | 各部門使用情境（驗證用） |
| [DB Schema](../phase2/db-schema.md) | 資料庫結構 |
| [合約業務邏輯](../phase2/business-logic-contract.md) | 合約生命週期 |
| [審核流程邏輯](../phase2/business-logic-approval.md) | 審核簽核流程 |
| [權限控制機制](../phase2/permission-control.md) | 三層授權機制 |

## 參考資源

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [MCP Specification 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [PyPI - mcp](https://pypi.org/project/mcp/)
