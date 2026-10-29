from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Training Reminder Automation System"

    DATABASE_URL: str

    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: str
    MICROSOFT_REDIRECT_URI: str

    FRONTEND_URL: str = "http://localhost:3000"

    SECRET_KEY: str

    HR_EMAILS: str

    REDIS_URL: str = "redis://localhost:6379/0"

    # SMTP / Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_USE_TLS: bool = True

    # WhatsApp Cloud API Configuration
    WHATSAPP_API_URL: str
    WHATSAPP_PHONE_NUMBER_ID: str
    WHATSAPP_BUSINESS_ACCOUNT_ID: str
    WHATSAPP_ACCESS_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def microsoft_authority(self) -> str:
        return (
            f"https://login.microsoftonline.com/"
            f"{self.MICROSOFT_TENANT_ID}"
        )

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace(
            "postgresql+asyncpg://",
            "postgresql+psycopg://",
        )


settings = Settings()