from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.runtime import runtime

websocket_router = APIRouter()


@websocket_router.websocket("/ws/live")
async def live_websocket(websocket: WebSocket):
    await websocket.accept()
    runtime.websockets.add(websocket)
    await websocket.send_json(runtime.live_update().model_dump(mode="json"))
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        runtime.websockets.discard(websocket)

