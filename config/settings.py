"""
Central configuration module.
Reads from .env file and provides typed settings to all services.
"""
import json
import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """All configuration lives here. Values come from .env file."""

    # --- Service Profile ---
    SERVICE_PROFILE: str = "wrams"

    # --- Database ---
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5001
    DB_NAME: str = "wrams"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "Passw0rd"

    # --- Service Ports ---
    VISION_PLAYER_PORT: int = 8000
    ASSET_FILTER_PORT: int = 8001

    # --- External Java API ---
    JAVA_API_HOST: str = "localhost"
    JAVA_API_PORT: int = 49001

    # --- Storage ---
    FRAMES_STORAGE_DIR: str = "frames_storage"

    # --- Public URLs ---
    PUBLIC_VISION_PLAYER_URL: str = "http://localhost:8000"
    PUBLIC_ASSET_FILTER_URL: str = "http://localhost:8001"
    PUBLIC_UPLOAD_URL: str = "/api/frames/batch"
    REMOTE_UPLOAD_URL: str = ""

    # --- Server Bind ---
    SERVER_HOST: str = "0.0.0.0"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    @property
    def JAVA_API_URL(self) -> str:
        return f"http://{self.JAVA_API_HOST}:{self.JAVA_API_PORT}"

    def load_profile(self) -> dict:
        """Load the service profile JSON for the current SERVICE_PROFILE."""
        profile_dir = os.path.join(os.path.dirname(__file__), "profiles")
        profile_path = os.path.join(profile_dir, f"{self.SERVICE_PROFILE}.json")
        if not os.path.exists(profile_path):
            raise FileNotFoundError(
                f"Service profile '{self.SERVICE_PROFILE}' not found at {profile_path}. "
                f"Available profiles: {os.listdir(profile_dir)}"
            )
        with open(profile_path, "r", encoding="utf-8") as f:
            return json.load(f)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        # Search for .env from the project root
        env_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
        )


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton — call this anywhere to get config."""
    return Settings()
