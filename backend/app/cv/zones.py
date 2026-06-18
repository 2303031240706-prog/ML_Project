from app.cv.density import classify_density
from app.models.schemas import ZoneMetric


DEFAULT_ZONE_CAPACITY = 80


def build_zone_metrics(camera_id: str, people_count: int) -> list[ZoneMetric]:
    weights = [0.32, 0.28, 0.24, 0.16]
    names = ["Entry", "Center", "Exit", "Perimeter"]
    zones: list[ZoneMetric] = []
    for index, weight in enumerate(weights):
        count = int(people_count * weight)
        capacity = DEFAULT_ZONE_CAPACITY if index != 1 else 100
        density_ratio = round(min(count / capacity, 1.25), 3)
        zones.append(
            ZoneMetric(
                zone_id=f"{camera_id}-zone-{index + 1}",
                name=names[index],
                people_count=count,
                capacity=capacity,
                density_ratio=density_ratio,
                density_level=classify_density(density_ratio),
            )
        )
    return zones

