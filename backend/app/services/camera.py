import asyncio
import math
import random
from datetime import datetime, timezone

from app.core.settings import settings
from app.cv.density import classify_density, risk_score
from app.cv.detector import PersonDetector
from app.cv.tracker import SimpleIoUTracker
from app.cv.zones import build_zone_metrics
from app.models.schemas import CameraState
from app.services.behavior import detect_abnormal_events
from app.services.prediction import CrowdPredictor


class CameraWorker:
    def __init__(
        self,
        camera_id: str,
        name: str,
        source: str,
        predictor: CrowdPredictor,
        detector: PersonDetector,
    ) -> None:
        self.camera_id = camera_id
        self.name = name
        self.source = source
        self.predictor = predictor
        self.detector = detector
        self.tracker = SimpleIoUTracker()
        self.capacity = 220
        self.tick = random.randint(0, 100)
        self.state = CameraState(camera_id=camera_id, name=name, source=source)
        self.running = False

    async def run(self, on_update) -> None:
        self.running = True
        while self.running:
            self.state = self._simulate_state()
            self.predictor.add_observation(self.camera_id, self.state.people_count)
            predicted, prediction_level, growth_rate = self.predictor.predict(self.camera_id, self.capacity)
            self.state.predicted_people_count = predicted
            self.state.prediction_level = prediction_level
            self.state.abnormal_events = detect_abnormal_events(
                self.state.people_count,
                predicted,
                self.state.density_ratio,
                growth_rate,
            )
            self.state.risk_score = risk_score(
                self.state.density_ratio,
                growth_rate,
                len(self.state.abnormal_events),
            )
            self.state.updated_at = datetime.now(timezone.utc)
            await on_update(self.state)
            await asyncio.sleep(2)

    def stop(self) -> None:
        self.running = False

    def _simulate_state(self) -> CameraState:
        self.tick += 1
        base = 55 + 35 * math.sin(self.tick / 8)
        rush = 65 if self.tick % 80 > 58 else 0
        noise = random.randint(-8, 12)
        people_count = max(int(base + rush + noise), 0)
        density_ratio = round(min(people_count / self.capacity, 1.25), 3)
        return CameraState(
            camera_id=self.camera_id,
            name=self.name,
            source=self.source,
            online=True,
            people_count=people_count,
            density_level=classify_density(density_ratio),
            density_ratio=density_ratio,
            zones=build_zone_metrics(self.camera_id, people_count),
        )

