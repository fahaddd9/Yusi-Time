from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

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

    # ── Phase 6.5 — Web Push / VAPID config (Addendum §5.3, RULE B-07) ──────
    # Required for F1 browser push notification delivery via Web Push protocol.
    # Generate VAPID keys with: py-vapid --gen-key
    # VAPID_CLAIMS_SUBJECT must be a mailto: URI for push service identification.
    # All three are Optional so the app boots without them in dev/test environments
    # where push delivery is not exercised; push_service.py checks at send-time.
    vapid_public_key: Optional[str] = None
    vapid_private_key: Optional[str] = None
    vapid_claims_subject: Optional[str] = None  # e.g. "mailto:admin@yusitime.com"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
