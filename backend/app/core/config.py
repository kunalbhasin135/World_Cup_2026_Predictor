"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> project root is three levels up
PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PROFILES_DIR = DATA_DIR / "profiles"
PLAYERS_DIR = DATA_DIR / "players"
LIVE_DATA_DIR = DATA_DIR / "live"
PLACEHOLDER_DATA_DIR = DATA_DIR / "placeholder"
MODEL_DIR = PROJECT_ROOT / "backend" / "models" / "trained"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "World Cup 2026 Match Predictor"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    USE_HISTORICAL_FEATURES: bool = True

    # Comma-separated origins for CORS (React dev server default)
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Paths
    DATA_DIR: Path = DATA_DIR
    RAW_DATA_DIR: Path = RAW_DATA_DIR
    PROCESSED_DATA_DIR: Path = PROCESSED_DATA_DIR
    PROFILES_DIR: Path = PROFILES_DIR
    PLAYERS_DIR: Path = PLAYERS_DIR
    LIVE_DATA_DIR: Path = LIVE_DATA_DIR
    PLACEHOLDER_DATA_DIR: Path = PLACEHOLDER_DATA_DIR
    MODEL_DIR: Path = MODEL_DIR

    # Optional live data (https://www.api-football.com/documentation-v3)
    API_FOOTBALL_KEY: str = ""
    API_FOOTBALL_BASE_URL: str = "https://v3.football.api-sports.io"
    API_FOOTBALL_SEASON: int = 2025
    MATCHUP_CONTEXT_SIMULATIONS: int = 250


settings = Settings()
