from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    app_env: str = "development"
    database_url: str
    test_database_url: str
    jwt_secret: str
    jwt_refresh_secret: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    invite_link_expire_hours: int = 168      # 7 days per PRD v1.3
    google_client_id: str
    google_client_secret: str
    aws_ses_region: str = "us-east-1"
    aws_access_key_id: str
    aws_secret_access_key: str
    frontend_url: str

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
