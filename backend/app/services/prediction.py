from collections import deque

from app.cv.density import classify_density
from app.models.schemas import DensityLevel


class CrowdPredictor:
    def __init__(self, window_size: int = 24) -> None:
        self.window_size = window_size
        self.history: dict[str, deque[int]] = {}

    def add_observation(self, camera_id: str, people_count: int) -> None:
        if camera_id not in self.history:
            self.history[camera_id] = deque(maxlen=self.window_size)
        self.history[camera_id].append(people_count)

    def predict(self, camera_id: str, capacity: int) -> tuple[int, DensityLevel, float]:
        values = list(self.history.get(camera_id, []))
        if not values:
            return 0, DensityLevel.safe, 0.0
        if len(values) < 3:
            predicted = values[-1]
            growth_rate = 0.0
        else:
            recent = values[-6:]
            slope = (recent[-1] - recent[0]) / max(len(recent) - 1, 1)
            predicted = max(int(recent[-1] + slope * 5), 0)
            growth_rate = slope / max(capacity, 1)
        density_ratio = min(predicted / max(capacity, 1), 1.25)
        return predicted, classify_density(density_ratio), round(growth_rate, 4)

