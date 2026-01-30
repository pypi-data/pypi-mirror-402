# ECS Contract Management MCP Server

ECS 合約管理系統的 MCP (Model Context Protocol) Server，提供安全的資料查詢能力。

## 安裝

### 前置需求

- Python 3.11+
- ODBC Driver 18 for SQL Server
- 可存取 ECS 資料庫

### 安裝步驟

```bash
# 進入專案目錄
cd /path/to/ECS

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或 .venv\Scripts\activate  # Windows

# 安裝依賴
pip install -e ".[dev]"
# 或
pip install -r requirements.txt
```

### 環境設定

```bash
# 複製範例設定檔
cp .env.example .env

# 編輯 .env 填入正確的資料庫連線資訊
```

## 使用方式

### 直接執行

```bash
python -m mcp_server
```

### 配合 Claude Desktop

在 Claude Desktop 的設定檔 `claude_desktop_config.json` 中加入：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ecs-contract": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/path/to/ECS",
      "env": {
        "DB_SERVER": "ecs2022.ltc",
        "DB_NAME": "LT_ECS_LTCCore",
        "DB_USER": "ecs_user",
        "DB_PASSWORD": "your_password",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

或者使用 uv：

```json
{
  "mcpServers": {
    "ecs-contract": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/ECS", "python", "-m", "mcp_server"],
      "env": {
        "DB_SERVER": "ecs2022.ltc",
        "DB_NAME": "LT_ECS_LTCCore",
        "DB_USER": "ecs_user",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

## 安全機制

### View 白名單

只允許查詢 `view` schema 下的授權 View，共 37 個：

- 合約相關：`view.Contract`, `view.ContractAttachment`, `view.ContractHistory` 等
- 組織相關：`view.Partner`, `view.Department`, `view.User` 等
- 流程相關：`view.ExamStatus`, `view.Acting` 等

完整清單見 `mcp_server/database/allowed_views.py`。

### SQL 驗證

- 只允許 SELECT 語句
- 禁止危險關鍵字（INSERT, UPDATE, DELETE, DROP 等）
- 禁止 SQL 註解
- 自動限制回傳筆數（預設 1000 筆）

### 稽核日誌

所有查詢都會記錄：
- SQL 語句
- 查詢目的
- 回傳筆數
- 執行時間
- 成功/失敗狀態

## 開發

### 執行測試

```bash
pytest
```

### 程式碼檢查

```bash
ruff check .
mypy mcp_server
```

## 相關文件

- [開發計劃](../docs/dev.md)
- [MCP 設計規格](../docs/dev-mcp-design.md)
- [View 欄位說明](../docs/dev-mcp-views.md)
- [安全機制](../docs/dev-security.md)
