from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class DensityLevel(str, Enum):
    safe = "Safe"
    warning = "Warning"
    danger = "Danger"
    critical = "Critical"


class AlertStatus(str, Enum):
    active = "active"
    acknowledged = "acknowledged"
    resolved = "resolved"


class ZoneMetric(BaseModel):
    zone_id: str
    name: str
    people_count: int
    capacity: int
    density_ratio: float
    density_level: DensityLevel


class CameraState(BaseModel):
    camera_id: str
    name: str
    source: str
    online: bool = True
    people_count: int = 0
    density_level: DensityLevel = DensityLevel.safe
    density_ratio: float = 0
    risk_score: float = 0
    prediction_level: DensityLevel = DensityLevel.safe
    predicted_people_count: int = 0
    abnormal_events: list[str] = Field(default_factory=list)
    zones: list[ZoneMetric] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Alert(BaseModel):
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    camera_id: str
    camera_name: str
    level: DensityLevel
    status: AlertStatus = AlertStatus.active
    title: str
    message: str
    people_count: int
    density_ratio: float
    recommended_action: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalyticsSummary(BaseModel):
    total_cameras: int
    online_cameras: int
    active_alerts: int
    total_people_count: int
    average_risk_score: float
    highest_risk_camera: str | None
    density_distribution: dict[str, int]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LiveUpdate(BaseModel):
    cameras: list[CameraState]
    alerts: list[Alert]
    summary: AnalyticsSummary
