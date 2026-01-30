# ECS MCP Server - 基礎設施

> 依賴管理、錯誤處理、日誌配置、連線池、重試機制

返回 [dev.md](dev.md)

---

## 依賴管理

### pyproject.toml

```toml
[project]
name = "ecs-mcp-server"
version = "0.1.0"
description = "ECS Contract Management MCP Server"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "mcp>=1.0.0,<2.0.0",
    "pyodbc>=5.2.0",
    "pydantic>=2.0.0,<3.0.0",
    "pydantic-settings>=2.0.0",
    "structlog>=24.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### requirements.txt（鎖定版本，供 pip install -r 使用）

```
# MCP SDK
mcp>=1.0.0,<2.0.0

# 資料庫
pyodbc>=5.2.0

# 資料驗證
pydantic>=2.0.0,<3.0.0
pydantic-settings>=2.0.0

# 日誌
structlog>=24.0.0

# 測試
pytest>=8.0.0
pytest-asyncio>=0.23.0

# 開發工具
ruff>=0.4.0
mypy>=1.10.0
```

---

## 統一回傳格式

所有 Tool 統一使用以下回傳結構：

```python
# tools/base.py
from pydantic import BaseModel
from typing import TypeVar, Generic, Optional
from datetime import datetime

T = TypeVar('T')

class ToolResponse(BaseModel, Generic[T]):
    """統一的 Tool 回傳格式"""
    success: bool
    data: Optional[T] = None
    metadata: dict = {}
    error: Optional[dict] = None

    @classmethod
    def ok(cls, data: T, total_count: int = 0) -> "ToolResponse[T]":
        return cls(
            success=True,
            data=data,
            metadata={
                "query_time": datetime.utcnow().isoformat() + "Z",
                "total_count": total_count
            },
            error=None
        )

    @classmethod
    def fail(cls, code: str, message: str, details: dict = None) -> "ToolResponse":
        return cls(
            success=False,
            data=None,
            metadata={"query_time": datetime.utcnow().isoformat() + "Z"},
            error={
                "code": code,
                "message": message,
                "details": details or {}
            }
        )
```

**成功回傳範例**：

```json
{
  "success": true,
  "data": {
    "contracts": [...]
  },
  "metadata": {
    "query_time": "2024-02-14T10:30:00Z",
    "total_count": 25
  },
  "error": null
}
```

**錯誤回傳範例**：

```json
{
  "success": false,
  "data": null,
  "metadata": {
    "query_time": "2024-02-14T10:30:00Z"
  },
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "無權存取此部門的合約資料",
    "details": {"department_id": 5}
  }
}
```

### query_database 專用格式

> **注意**：`query_database` Tool 使用專用的回傳格式，以更好地呈現 SQL 查詢結果。
> 詳細格式定義請參考 [dev-mcp-design.md](dev-mcp-design.md#query_database)。

```json
{
    "success": true,
    "columns": ["ContractId", "Title", "ValidEndDate"],
    "rows": [
        [12345, "採購合約-台積電", "2024-03-15"],
        [12346, "服務合約-聯發科", "2024-03-20"]
    ],
    "row_count": 2,
    "truncated": false,
    "message": null
}
```

此格式與通用 `ToolResponse` 的差異：
- 使用 `columns` + `rows` 取代 `data`，更適合表格資料
- 使用 `row_count` + `truncated` 取代 `metadata.total_count`
- 使用 `message` 取代 `error`（錯誤時 success=false）

---

## 錯誤處理策略

### 錯誤代碼定義

```python
# utils/errors.py
from enum import Enum

class ErrorCode(str, Enum):
    # 驗證錯誤
    INVALID_PARAMETER = "INVALID_PARAMETER"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"

    # 權限錯誤
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHORIZED = "UNAUTHORIZED"

    # 安全錯誤（SQL 驗證相關）
    SECURITY_VIOLATION = "SECURITY_VIOLATION"        # 一般安全違規
    UNAUTHORIZED_TABLE = "UNAUTHORIZED_TABLE"        # 查詢非白名單 View
    DANGEROUS_SQL = "DANGEROUS_SQL"                  # 包含危險關鍵字
    SQL_COMMENT_NOT_ALLOWED = "SQL_COMMENT_NOT_ALLOWED"  # 包含 SQL 註解

    # 資料庫錯誤
    DB_CONNECTION_ERROR = "DB_CONNECTION_ERROR"
    DB_QUERY_ERROR = "DB_QUERY_ERROR"
    DB_TIMEOUT = "DB_TIMEOUT"

    # 資料錯誤
    NOT_FOUND = "NOT_FOUND"
    DATA_INTEGRITY_ERROR = "DATA_INTEGRITY_ERROR"

    # 系統錯誤
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ToolError(Exception):
    """Tool 專用例外"""
    def __init__(self, code: ErrorCode, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class SecurityError(ToolError):
    """安全驗證例外（SQL 驗證失敗時使用）"""
    def __init__(self, code: ErrorCode, message: str, sql: str = None):
        details = {"sql": sql} if sql else {}
        super().__init__(code, message, details)
```

### 全域錯誤處理

```python
# server.py
from functools import wraps
from utils.errors import ToolError, ErrorCode
from tools.base import ToolResponse

def handle_tool_errors(func):
    """Tool 錯誤處理裝飾器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ToolError as e:
            logger.warning(f"Tool error: {e.code} - {e.message}")
            return ToolResponse.fail(e.code, e.message, e.details)
        except pyodbc.OperationalError as e:
            logger.error(f"Database connection error: {e}")
            return ToolResponse.fail(
                ErrorCode.DB_CONNECTION_ERROR,
                "資料庫連線失敗，請稍後再試"
            )
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            return ToolResponse.fail(
                ErrorCode.INTERNAL_ERROR,
                "系統內部錯誤"
            )
    return wrapper
```

---

## 日誌配置

```python
# utils/logging.py
import structlog
import logging
from config import settings

def setup_logging():
    """配置 structlog"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.LOG_LEVEL)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 使用方式
logger = structlog.get_logger()
logger.info("tool_called", tool="contract_expiry_alert", params={"days_ahead": 90})
```

---

## 環境變數管理

```python
# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """應用程式配置"""

    # 資料庫
    DB_SERVER: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_POOL_SIZE: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_QUERY_TIMEOUT: int = 30

    # 日誌
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json | console
    LOG_FILE: str = "mcp_audit.log"  # 稽核日誌檔案

    # 重試
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: float = 1.0

    # Pydantic v2 配置方式
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
```

**.env 範例**（不納入版控）：

```
DB_SERVER=your-server.database.windows.net
DB_NAME=LT_ECS_LTCCore
DB_USER=readonly_user
DB_PASSWORD=your_secure_password
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=mcp_audit.log
```

---

## 連線池管理

採用 `pyodbc` + `asyncio.to_thread()` 方式，將同步驅動包裝成 async。

```python
# database/connection.py
import asyncio
import pyodbc
from queue import Queue, Empty
from contextlib import asynccontextmanager
from config import settings
from utils.logging import logger

class DatabasePool:
    """資料庫連線池管理（pyodbc + asyncio.to_thread）"""

    _pool: Queue = None
    _conn_str: str = None

    @classmethod
    async def init(cls):
        """初始化連線池"""
        cls._conn_str = (
            f"DRIVER={{{settings.DB_DRIVER}}};"
            f"SERVER={settings.DB_SERVER};"
            f"DATABASE={settings.DB_NAME};"
            f"UID={settings.DB_USER};"
            f"PWD={settings.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
        )
        cls._pool = Queue(maxsize=settings.DB_POOL_SIZE)

        # 預先建立連線
        for _ in range(settings.DB_POOL_SIZE):
            conn = await asyncio.to_thread(pyodbc.connect, cls._conn_str)
            cls._pool.put(conn)

        logger.info("database_pool_initialized", pool_size=settings.DB_POOL_SIZE)

    @classmethod
    async def close(cls):
        """關閉連線池"""
        while not cls._pool.empty():
            try:
                conn = cls._pool.get_nowait()
                await asyncio.to_thread(conn.close)
            except Empty:
                break
        logger.info("database_pool_closed")

    @classmethod
    @asynccontextmanager
    async def get_connection(cls):
        """取得連線"""
        conn = None
        try:
            conn = cls._pool.get(timeout=settings.DB_POOL_TIMEOUT)
            yield conn
        finally:
            if conn:
                cls._pool.put(conn)

    @classmethod
    async def execute_query(cls, sql: str) -> tuple[list, list]:
        """執行查詢（async 包裝）"""
        async with cls.get_connection() as conn:
            def _execute():
                cursor = conn.cursor()
                cursor.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()
                return columns, [list(row) for row in rows]

            return await asyncio.to_thread(_execute)
```

---

## 重試機制

```python
# utils/retry.py
import asyncio
from functools import wraps
from config import settings
from utils.logging import logger

def with_retry(max_attempts: int = None, delay: float = None):
    """重試裝飾器（針對暫時性錯誤）"""
    max_attempts = max_attempts or settings.RETRY_MAX_ATTEMPTS
    delay = delay or settings.RETRY_DELAY_SECONDS

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except (pyodbc.OperationalError, pyodbc.InterfaceError) as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            "db_retry",
                            attempt=attempt,
                            max_attempts=max_attempts,
                            error=str(e)
                        )
                        await asyncio.sleep(delay * attempt)  # 指數退避
                    else:
                        raise
            raise last_exception
        return wrapper
    return decorator
```
