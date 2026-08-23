from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "CampusOne"
    environment: str = "development"
    database_url: str = "sqlite:///./campusone.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 60 * 24 * 7
    campus_email_domain: str = "@stu.manit.ac.in"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ]

    # Brevo HTTP REST API Configuration
    brevo_api_key: str = ""
    brevo_sender_email: str = ""
    email_otp_expire_minutes: int = 10

    @property
    def BREVO_API_KEY(self) -> str:
        return self.brevo_api_key

    @property
    def BREVO_SENDER_EMAIL(self) -> str:
        return self.brevo_sender_email

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
