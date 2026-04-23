from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Family Photo Gallery"
    data_dir: Path = Path("backend/data")
    photos_root: Path = Path("backend/photos_root")
    token_ttl_days: int = 7
    scan_interval_seconds: int = 300
    admin_default_username: str = "admin"
    admin_default_password: str = "admin123"

    model_config = SettingsConfigDict(env_prefix="GALLERY_", extra="ignore")


settings = Settings()
