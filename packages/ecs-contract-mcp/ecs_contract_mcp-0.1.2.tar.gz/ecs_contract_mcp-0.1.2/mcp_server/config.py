"""Configuration management using environment variables"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables"""

    # Database settings (must be set via environment variables)
    DB_SERVER: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_DRIVER: str = "ODBC Driver 18 for SQL Server"
    DB_POOL_SIZE: int = 5
    DB_POOL_TIMEOUT: int = 30
    DB_QUERY_TIMEOUT: int = 30

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "console"  # json | console
    LOG_FILE: str = "mcp_audit.log"

    # Query limits
    MAX_ROWS: int = 1000

    # Retry settings
    RETRY_MAX_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: float = 1.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def connection_string(self) -> str:
        """Build ODBC connection string"""
        return (
            f"DRIVER={{{self.DB_DRIVER}}};"
            f"SERVER={self.DB_SERVER};"
            f"DATABASE={self.DB_NAME};"
            f"UID={self.DB_USER};"
            f"PWD={self.DB_PASSWORD};"
            "TrustServerCertificate=yes;"
            "Encrypt=no;"
        )


# Singleton instance
settings = Settings()
