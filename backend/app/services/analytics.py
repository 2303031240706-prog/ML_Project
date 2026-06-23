from app.models.schemas import AnalyticsSummary, CameraState
from app.services.alerts import AlertService


def build_summary(cameras: list[CameraState], alert_service: AlertService) -> AnalyticsSummary:
    distribution = {"Safe": 0, "Warning": 0, "Danger": 0, "Critical": 0}
    for camera in cameras:
        distribution[camera.density_level.value] += 1
    highest = max(cameras, key=lambda item: item.risk_score, default=None)
    average_risk = sum(camera.risk_score for camera in cameras) / len(cameras) if cameras else 0
    return AnalyticsSummary(
        total_cameras=len(cameras),
        online_cameras=sum(1 for camera in cameras if camera.online),
        active_alerts=len(alert_service.active_alerts()),
        total_people_count=sum(camera.people_count for camera in cameras),
        average_risk_score=round(average_risk, 1),
        highest_risk_camera=highest.name if highest else None,
        density_distribution=distribution,
    )
