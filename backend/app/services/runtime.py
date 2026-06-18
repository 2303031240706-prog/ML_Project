import asyncio

from app.core.settings import settings
from app.cv.detector import PersonDetector
from app.models.schemas import CameraState, LiveUpdate
from app.services.alerts import AlertService
from app.services.analytics import build_summary
from app.services.camera import CameraWorker
from app.services.prediction import CrowdPredictor


class Runtime:
    def __init__(self) -> None:
        self.predictor = CrowdPredictor()
        self.detector = PersonDetector()
        self.alerts = AlertService()
        self.cameras: dict[str, CameraState] = {}
        self.workers: list[CameraWorker] = []
        self.tasks: list[asyncio.Task] = []
        self.websockets: set = set()

    async def start(self) -> None:
        for index, (name, source) in enumerate(settings.camera_sources, start=1):
            camera_id = f"cam-{index}"
            worker = CameraWorker(camera_id, name, source, self.predictor, self.detector)
            self.workers.append(worker)
            self.cameras[camera_id] = worker.state
            self.tasks.append(asyncio.create_task(worker.run(self.on_camera_update)))

    async def stop(self) -> None:
        for worker in self.workers:
            worker.stop()
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def on_camera_update(self, state: CameraState) -> None:
        self.cameras[state.camera_id] = state
        await self.alerts.evaluate(state)
        await self.broadcast()

    def live_update(self) -> LiveUpdate:
        cameras = list(self.cameras.values())
        return LiveUpdate(
            cameras=cameras,
            alerts=self.alerts.alerts[:20],
            summary=build_summary(cameras, self.alerts),
        )

    async def broadcast(self) -> None:
        if not self.websockets:
            return
        payload = self.live_update().model_dump(mode="json")
        disconnected = []
        for websocket in self.websockets:
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.websockets.discard(websocket)


runtime = Runtime()

