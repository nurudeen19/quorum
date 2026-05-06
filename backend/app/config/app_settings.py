"""Application identity and runtime flags"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


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
    
    # ========================
    # Authentication & JWT
    # ========================
    jwt_secret: str = Field(default="change-me", min_length=8, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, alias="JWT_EXPIRE_MINUTES")
    auth_dev_auto_verify_email: bool = Field(default=False, alias="AUTH_DEV_AUTO_VERIFY_EMAIL")
    
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

app_settings = AppSettings()