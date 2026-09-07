"""Application settings, loaded from environment variables / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    chroma_persist_dir: str = "./data/chroma"
    data_dir: str = "./data"
    google_client_secret_file: str = "./secrets/client_secret.json"
    google_token_file: str = "./secrets/token.json"
    drive_inbox_folder_id: str = ""
    drive_exports_folder_id: str = ""
    drive_poll_interval_seconds: int = 300

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
