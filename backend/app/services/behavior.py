def detect_abnormal_events(
    current_count: int,
    predicted_count: int,
    density_ratio: float,
    growth_rate: float,
) -> list[str]:
    events: list[str] = []
    if growth_rate > 0.035 and current_count > 30:
        events.append("sudden_gathering")
    if predicted_count > current_count * 1.35 and current_count > 20:
        events.append("crowd_surge_risk")
    if density_ratio > 0.82 and growth_rate > 0.015:
        events.append("stampede_risk")
    return events

