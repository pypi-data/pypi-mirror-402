"""Database connection pool management using pyodbc with asyncio"""

import asyncio
from contextlib import asynccontextmanager
from queue import Empty, Queue
from typing import Any, AsyncGenerator

import pyodbc

from mcp_server.config import settings
from mcp_server.utils.errors import DatabaseError, ErrorCode
from mcp_server.utils.logging import get_logger

logger = get_logger(__name__)


class DatabasePool:
    """Database connection pool manager (pyodbc + asyncio.to_thread)"""

    _pool: Queue[pyodbc.Connection] | None = None
    _initialized: bool = False

    @classmethod
    async def init(cls) -> None:
        """Initialize the connection pool"""
        if cls._initialized:
            logger.debug("database_pool_already_initialized")
            return

        cls._pool = Queue(maxsize=settings.DB_POOL_SIZE)

        # Pre-create connections
        conn_str = settings.connection_string
        logger.info("database_pool_initializing", pool_size=settings.DB_POOL_SIZE)

        try:
            for i in range(settings.DB_POOL_SIZE):
                conn = await asyncio.to_thread(pyodbc.connect, conn_str)
                cls._pool.put(conn)
                logger.debug("connection_created", index=i)
        except pyodbc.Error as e:
            logger.error("database_pool_init_failed", error=str(e))
            raise DatabaseError(
                ErrorCode.DB_CONNECTION_ERROR,
                f"Failed to initialize database pool: {e}",
                original_error=e,
            )

        cls._initialized = True
        logger.info("database_pool_initialized", pool_size=settings.DB_POOL_SIZE)

    @classmethod
    async def close(cls) -> None:
        """Close all connections in the pool"""
        if not cls._pool:
            return

        closed_count = 0
        while not cls._pool.empty():
            try:
                conn = cls._pool.get_nowait()
                await asyncio.to_thread(conn.close)
                closed_count += 1
            except Empty:
                break
            except Exception as e:
                logger.warning("connection_close_error", error=str(e))

        cls._initialized = False
        logger.info("database_pool_closed", closed_count=closed_count)

    @classmethod
    @asynccontextmanager
    async def get_connection(cls) -> AsyncGenerator[pyodbc.Connection, None]:
        """Get a connection from the pool

        Yields:
            A database connection

        Raises:
            DatabaseError: If unable to get a connection
        """
        if not cls._pool or not cls._initialized:
            raise DatabaseError(
                ErrorCode.DB_CONNECTION_ERROR,
                "Database pool not initialized",
            )

        conn: pyodbc.Connection | None = None
        try:
            conn = cls._pool.get(timeout=settings.DB_POOL_TIMEOUT)
            yield conn
        except Empty:
            raise DatabaseError(
                ErrorCode.DB_TIMEOUT,
                f"Timeout waiting for database connection (pool exhausted after {settings.DB_POOL_TIMEOUT}s)",
            )
        finally:
            if conn:
                try:
                    # Return connection to pool
                    cls._pool.put(conn)
                except Exception as e:
                    logger.warning("connection_return_error", error=str(e))

    @classmethod
    async def execute_query(
        cls,
        sql: str,
        timeout: int | None = None,
    ) -> tuple[list[str], list[list[Any]]]:
        """Execute a query and return results

        Args:
            sql: The SQL query to execute
            timeout: Query timeout in seconds (default: settings.DB_QUERY_TIMEOUT)

        Returns:
            Tuple of (column_names, rows)

        Raises:
            DatabaseError: If the query fails
        """
        timeout = timeout or settings.DB_QUERY_TIMEOUT

        async with cls.get_connection() as conn:

            def _execute() -> tuple[list[str], list[list[Any]]]:
                cursor = conn.cursor()
                cursor.execute(sql)

                if cursor.description is None:
                    return [], []

                columns = [desc[0] for desc in cursor.description]
                rows = [list(row) for row in cursor.fetchall()]
                cursor.close()
                return columns, rows

            try:
                return await asyncio.wait_for(
                    asyncio.to_thread(_execute),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                raise DatabaseError(
                    ErrorCode.DB_TIMEOUT,
                    f"Query timeout after {timeout} seconds",
                )
            except pyodbc.Error as e:
                logger.error("query_execution_error", error=str(e), sql=sql[:200])
                raise DatabaseError(
                    ErrorCode.DB_QUERY_ERROR,
                    f"Query execution failed: {e}",
                    original_error=e,
                )

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the pool is initialized"""
        return cls._initialized

    @classmethod
    def pool_status(cls) -> dict[str, Any]:
        """Get pool status information"""
        if not cls._pool:
            return {
                "initialized": False,
                "available": 0,
                "total": 0,
            }
        return {
            "initialized": cls._initialized,
            "available": cls._pool.qsize(),
            "total": settings.DB_POOL_SIZE,
        }
