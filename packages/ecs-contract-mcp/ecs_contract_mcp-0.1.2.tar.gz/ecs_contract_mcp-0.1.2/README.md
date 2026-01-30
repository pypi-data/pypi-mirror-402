# ECS Contract MCP Server

ECS 合約管理系統的 MCP (Model Context Protocol) Server，讓 Claude Desktop 能夠安全地查詢合約資料庫。

## 安裝方式

### 方式一：使用 uvx（推薦）

最簡單的安裝方式，不需要手動管理 Python 環境。

```bash
uvx ecs-contract-mcp
```

### 方式二：使用 pip

```bash
pip install ecs-contract-mcp
```

---

## Claude Desktop 配置

### Windows 11

**步驟 1：安裝前置需求**

1. **安裝 uv**（Python 套件管理器）
   ```powershell
   # 使用 PowerShell（管理員權限）
   irm https://astral.sh/uv/install.ps1 | iex
   ```
   或
   ```powershell
   pip install uv
   ```

2. **安裝 ODBC Driver 18 for SQL Server**
   - 下載連結：https://go.microsoft.com/fwlink/?linkid=2249006
   - 執行安裝程式，使用預設選項即可

**步驟 2：配置 Claude Desktop**

編輯配置檔（路徑：`%APPDATA%\Claude\claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "ecs": {
      "command": "C:\\Users\\你的使用者名稱\\.local\\bin\\uvx.exe",
      "args": ["ecs-contract-mcp"],
      "env": {
        "DB_SERVER": "your_server_address",
        "DB_NAME": "your_database_name",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

> **注意**：請將 `你的使用者名稱` 替換為你的 Windows 使用者名稱。

**步驟 3：重啟 Claude Desktop**

關閉並重新開啟 Claude Desktop，即可使用。

---

### macOS

**步驟 1：安裝前置需求**

1. **安裝 uv**
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   或
   ```bash
   brew install uv
   ```

2. **安裝 ODBC Driver 18 for SQL Server**
   ```bash
   # 安裝 Homebrew（如果還沒有）
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

   # 加入 Microsoft 套件來源
   brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
   brew update

   # 安裝 ODBC Driver
   HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18
   ```

**步驟 2：配置 Claude Desktop**

編輯配置檔（路徑：`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "ecs": {
      "command": "uvx",
      "args": ["ecs-contract-mcp"],
      "env": {
        "DB_SERVER": "your_server_address",
        "DB_NAME": "your_database_name",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password"
      }
    }
  }
}
```

**步驟 3：重啟 Claude Desktop**

關閉並重新開啟 Claude Desktop，即可使用。

---

## 環境變數說明

| 變數 | 必填 | 預設值 | 說明 |
|------|:----:|--------|------|
| `DB_SERVER` | ✅ | - | SQL Server 主機位址 |
| `DB_NAME` | ✅ | - | 資料庫名稱 |
| `DB_USER` | ✅ | - | 資料庫使用者帳號 |
| `DB_PASSWORD` | ✅ | - | 資料庫密碼 |
| `DB_DRIVER` | ❌ | `ODBC Driver 18 for SQL Server` | ODBC 驅動程式名稱 |
| `LOG_LEVEL` | ❌ | `INFO` | 日誌等級（DEBUG/INFO/WARNING/ERROR）|
| `MAX_ROWS` | ❌ | `1000` | 查詢結果上限筆數 |

---

## 驗證安裝

在 Claude Desktop 中輸入：

```
請執行 health_check 確認 MCP Server 連線狀態
```

如果配置正確，會回傳資料庫連線狀態。

---

## 常見問題

### Windows

| 問題 | 解決方案 |
|------|---------|
| `uvx` 指令找不到 | 重新開啟 PowerShell，或檢查 PATH 環境變數 |
| ODBC Driver 找不到 | 確認已安裝 "ODBC Driver 18 for SQL Server" |
| 連線逾時 | 確認防火牆允許連線到 SQL Server（預設 Port 1433）|

### macOS

| 問題 | 解決方案 |
|------|---------|
| `uvx` 指令找不到 | 執行 `source ~/.zshrc` 或重開終端機 |
| ODBC Driver 安裝失敗 | 嘗試 `brew update && brew upgrade` 後重試 |
| SSL 憑證錯誤 | 環境變數已設定 `TrustServerCertificate=yes` |

---

## 開發者指南

### 本地開發

```bash
# Clone 專案
git clone https://github.com/your-org/ECS.git
cd ECS

# 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安裝開發依賴
pip install -e ".[dev]"

# 複製環境設定
cp .env.example .env
# 編輯 .env 填入資料庫連線資訊

# 執行測試
pytest

# 啟動 MCP Server
python -m mcp_server
```

### 專案結構

```
mcp_server/
├── server.py              # MCP Server 入口
├── config.py              # 環境變數配置
├── database/              # 資料庫連線與查詢
├── resources/             # MCP Resources（背景知識）
├── tools/                 # MCP Tools（查詢能力）
├── prompts/               # MCP Prompts（分析指引）
└── utils/                 # 工具函數
```

---

## 文件

- [MCP 設計規格](docs/design/mcp-design.md)
- [View 欄位說明](docs/design/mcp-views.md)
- [安全機制](docs/design/security.md)
- [開發日誌](docs/development-journal.md)

---

## 授權

本專案為內部使用。

---

## 連結

- **PyPI**: https://pypi.org/project/ecs-contract-mcp/
- **MCP 官方文件**: https://modelcontextprotocol.io/
