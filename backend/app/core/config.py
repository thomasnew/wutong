from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Family Photo Gallery"
    database_url: str = "mysql+pymysql://wutong:wutong@127.0.0.1:3306/wutong"
    photos_root: Path = Path("backend/photos_root")
    static_root: Path | None = None
    token_ttl_days: int = 7
    scan_interval_seconds: int = 300
    admin_default_username: str = "admin"
    admin_default_password: str = "admin123"

    model_config = SettingsConfigDict(env_prefix="GALLERY_", extra="ignore")


settings = Settings()
