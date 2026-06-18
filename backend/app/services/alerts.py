from datetime import datetime, timezone

import httpx

from app.core.settings import settings
from app.models.schemas import Alert, AlertStatus, CameraState, DensityLevel


class AlertService:
    def __init__(self) -> None:
        self.alerts: list[Alert] = []
        self._last_level_by_camera: dict[str, DensityLevel] = {}

    async def evaluate(self, camera: CameraState) -> Alert | None:
        should_alert = camera.density_level in {
            DensityLevel.warning,
            DensityLevel.danger,
            DensityLevel.critical,
        } or camera.prediction_level in {DensityLevel.danger, DensityLevel.critical}

        previous_level = self._last_level_by_camera.get(camera.camera_id)
        self._last_level_by_camera[camera.camera_id] = camera.density_level
        if not should_alert or previous_level == camera.density_level:
            return None

        alert = Alert(
            camera_id=camera.camera_id,
            camera_name=camera.name,
            level=camera.density_level,
            title=f"{camera.density_level.value} crowd level at {camera.name}",
            message=(
                f"{camera.people_count} people detected. "
                f"Predicted count: {camera.predicted_people_count}. "
                f"Events: {', '.join(camera.abnormal_events) or 'none'}."
            ),
            people_count=camera.people_count,
            density_ratio=camera.density_ratio,
            recommended_action=self._recommended_action(camera),
            metadata={"risk_score": camera.risk_score, "prediction_level": camera.prediction_level},
        )
        self.alerts.insert(0, alert)
        self.alerts = self.alerts[:100]
        await self._notify_control_room(alert)
        return alert

    def active_alerts(self) -> list[Alert]:
        return [alert for alert in self.alerts if alert.status == AlertStatus.active]

    def acknowledge(self, alert_id: str) -> Alert | None:
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.acknowledged
                alert.acknowledged_at = datetime.now(timezone.utc)
                return alert
        return None

    def _recommended_action(self, camera: CameraState) -> str:
        if camera.density_level == DensityLevel.critical or "stampede_risk" in camera.abnormal_events:
            return "Dispatch field team immediately and open diversion routes."
        if camera.density_level == DensityLevel.danger:
            return "Deploy officers and restrict incoming flow to the zone."
        if camera.prediction_level in {DensityLevel.danger, DensityLevel.critical}:
            return "Issue preventive alert and prepare crowd diversion."
        return "Monitor closely and notify local staff."

    async def _notify_control_room(self, alert: Alert) -> None:
        if not settings.alert_webhook_url:
            return
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                await client.post(settings.alert_webhook_url, json=alert.model_dump(mode="json"))
        except Exception:
            return

