from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    redis_url: str = "redis://redis:6379/0"
    download_dir: str = "/tmp/ytdownloads"
    max_file_age_minutes: int = 30
    max_concurrent_downloads: int = 3
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8000"]
    ytdlp_cookies_file: Optional[str] = None
    ytdlp_proxy: Optional[str] = None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

os.makedirs(settings.download_dir, exist_ok=True)
