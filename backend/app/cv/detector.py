from dataclasses import dataclass
from typing import Any

from app.core.settings import settings


@dataclass
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_name: str = "person"


class PersonDetector:
    def __init__(self) -> None:
        self.model = None
        self.enabled = False
        if settings.simulation_mode:
            return
        try:
            from ultralytics import YOLO

            self.model = YOLO(settings.yolo_model_path)
            self.enabled = True
        except Exception:
            self.model = None
            self.enabled = False

    def detect(self, frame: Any) -> list[Detection]:
        if not self.enabled or self.model is None:
            return []

        results = self.model.predict(
            frame,
            conf=settings.person_confidence,
            classes=[0],
            verbose=False,
        )
        detections: list[Detection] = []
        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                detections.append(Detection(x1, y1, x2, y2, confidence))
        return detections
