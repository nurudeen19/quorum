"""Application identity and runtime flags"""

from __future__ import annotations

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class AppSettings(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    app_name: str = Field(default="Quorum", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    jwt_secret: str = Field(default="change-me", min_length=8, alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60 * 24 * 7, alias="JWT_EXPIRE_MINUTES")
    frontend_app_base_url: str = Field(default="http://localhost:5173", alias="FRONTEND_APP_BASE_URL")
    mailtrap_api_token: str | None = Field(default=None, alias="MAILTRAP_API_TOKEN")
    mail_from_email: str = Field(default="noreply@example.com", alias="MAIL_FROM_EMAIL")
    mail_from_name: str = Field(default="Quorum", alias="MAIL_FROM_NAME")
    auth_dev_auto_verify_email: bool = Field(default=False, alias="AUTH_DEV_AUTO_VERIFY_EMAIL")
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        alias="CORS_ORIGINS",
        description="Comma-separated origins.",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.cors_origins_raw.split(",") if o.strip()]

app_settings = AppSettings()