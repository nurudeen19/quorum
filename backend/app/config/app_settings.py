"""Application identity and runtime flags"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AppSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # ========================
    # Application Identity
    # ========================
    app_name: str = Field(default="Quorum", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    
    # ========================
    # Database
    # ========================
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=10, ge=1, le=50, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=20, ge=0, le=100, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(default=30, ge=1, le=300, alias="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(default=3600, ge=300, alias="DATABASE_POOL_RECYCLE")
    
    # ========================
    # Authentication & JWT
    # ========================
    jwt_secret: str = Field(default="change-me", min_length=8, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_expire_minutes: int = Field(default=30, ge=5, le=24 * 60, alias="JWT_ACCESS_EXPIRE_MINUTES")
    jwt_refresh_expire_days: int = Field(default=7, ge=1, le=90, alias="JWT_REFRESH_EXPIRE_DAYS")
    auth_dev_auto_verify_email: bool = Field(default=False, alias="AUTH_DEV_AUTO_VERIFY_EMAIL")
    email_verification_expire_hours: int = Field(
        default=48, ge=1, le=168, alias="EMAIL_VERIFICATION_EXPIRE_HOURS"
    )
    password_reset_expire_minutes: int = Field(
        default=60, ge=15, le=24 * 60, alias="PASSWORD_RESET_EXPIRE_MINUTES"
    )
    
    # ========================
    # CORS & Frontend
    # ========================
    frontend_app_base_url: str = Field(default="http://localhost:5173", alias="FRONTEND_APP_BASE_URL")
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
        description="Comma-separated origins.",
    )
    
    # ========================
    # Email/Mail Configuration
    # ========================
    mailtrap_api_token: str | None = Field(default=None, alias="MAILTRAP_API_TOKEN")
    mail_from_email: str = Field(default="noreply@example.com", alias="MAIL_FROM_EMAIL")
    mail_from_name: str = Field(default="Quorum", alias="MAIL_FROM_NAME")
    
    # ========================
    # Logging Configuration
    # ========================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL", description="Logging level (e.g., INFO, DEBUG, WARNING)")
    log_mode: str = Field(default="both", alias="LOG_MODE", description="Logging mode: console, json, or both")
    log_file_path: str = Field(default="logs/app.log", alias="LOG_FILE_PATH", description="Path to log file")
    log_max_size_mb: int = Field(default=10, ge=1, le=100, alias="LOG_MAX_SIZE_MB", description="Max log file size in MB")
    log_backup_count: int = Field(default=5, ge=1, le=20, alias="LOG_BACKUP_COUNT", description="Number of backup log files")
    
    # ========================
    # Tracing/Observability
    # ========================
    otel_service_name: str = Field(default="quorum-api", alias="OTEL_SERVICE_NAME")
    otel_exporter_otlp_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # ========================
    # Metrics
    # ========================
    metrics_enabled: bool = Field(default=True, alias="METRICS_ENABLED")

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]