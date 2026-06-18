from dataclasses import dataclass

from app.cv.detector import Detection


@dataclass
class TrackedObject:
    track_id: int
    bbox: tuple[float, float, float, float]
    confidence: float


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    iw, ih = max(ix2 - ix1, 0), max(iy2 - iy1, 0)
    intersection = iw * ih
    area_a = max(ax2 - ax1, 0) * max(ay2 - ay1, 0)
    area_b = max(bx2 - bx1, 0) * max(by2 - by1, 0)
    union = area_a + area_b - intersection
    return intersection / union if union else 0


class SimpleIoUTracker:
    def __init__(self, iou_threshold: float = 0.3, max_missing_frames: int = 20) -> None:
        self.iou_threshold = iou_threshold
        self.max_missing_frames = max_missing_frames
        self.next_id = 1
        self.tracks: dict[int, tuple[tuple[float, float, float, float], int, float]] = {}

    def update(self, detections: list[Detection]) -> list[TrackedObject]:
        assigned_tracks: set[int] = set()
        output: list[TrackedObject] = []

        for detection in detections:
            bbox = (detection.x1, detection.y1, detection.x2, detection.y2)
            best_track_id = None
            best_score = 0.0
            for track_id, (track_bbox, missing, _) in self.tracks.items():
                if track_id in assigned_tracks or missing > self.max_missing_frames:
                    continue
                score = _iou(track_bbox, bbox)
                if score > best_score:
                    best_score = score
                    best_track_id = track_id

            if best_track_id is None or best_score < self.iou_threshold:
                best_track_id = self.next_id
                self.next_id += 1

            self.tracks[best_track_id] = (bbox, 0, detection.confidence)
            assigned_tracks.add(best_track_id)
            output.append(TrackedObject(best_track_id, bbox, detection.confidence))

        for track_id, (bbox, missing, confidence) in list(self.tracks.items()):
            if track_id not in assigned_tracks:
                missing += 1
                if missing > self.max_missing_frames:
                    del self.tracks[track_id]
                else:
                    self.tracks[track_id] = (bbox, missing, confidence)

        return output

