from app.core.settings import settings
from app.models.schemas import DensityLevel


def classify_density(density_ratio: float) -> DensityLevel:
    if density_ratio <= settings.safe_density_max:
        return DensityLevel.safe
    if density_ratio <= settings.warning_density_max:
        return DensityLevel.warning
    if density_ratio <= settings.danger_density_max:
        return DensityLevel.danger
    return DensityLevel.critical


def risk_score(density_ratio: float, growth_rate: float, abnormal_event_count: int) -> float:
    base = min(density_ratio, 1.0) * 70
    trend = min(max(growth_rate, 0), 1.0) * 20
    behavior = min(abnormal_event_count, 3) * 4
    return round(min(base + trend + behavior, 100), 2)

