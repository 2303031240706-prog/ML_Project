from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Smart Crowd Safety System"
    environment: str = "development"
    simulation_mode: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="CORS_ORIGINS",
    )

    yolo_model_path: str = "yolov8n.pt"
    person_confidence: float = 0.45
    frame_width: int = 1280
    frame_height: int = 720
    camera_sources_raw: str = Field(
        default="Main Gate|simulation://main-gate,Metro Platform|simulation://metro-platform",
        alias="CAMERA_SOURCES",
    )

    mongodb_uri: str | None = None
    mongodb_db: str = "smart_crowd_safety"
    redis_url: str | None = None
    alert_webhook_url: str | None = None

    safe_density_max: float = 0.35
    warning_density_max: float = 0.60
    danger_density_max: float = 0.82
    prediction_horizon_seconds: int = 300

    @property
    def cors_origins(self) -> list[str]:
        return [item.strip() for item in self.cors_origins_raw.split(",") if item.strip()]

    @property
    def camera_sources(self) -> list[tuple[str, str]]:
        sources: list[tuple[str, str]] = []
        for raw_source in self.camera_sources_raw.split(","):
            raw_source = raw_source.strip()
            if not raw_source:
                continue
            if "|" in raw_source:
                name, url = raw_source.split("|", 1)
            else:
                name, url = raw_source, raw_source
            sources.append((name.strip(), url.strip()))
        return sources


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

