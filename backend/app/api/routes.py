from fastapi import APIRouter, HTTPException

from app.services.runtime import runtime

router = APIRouter(prefix="/api")


@router.get("/cameras")
async def get_cameras():
    return list(runtime.cameras.values())


@router.get("/alerts")
async def get_alerts():
    return runtime.alerts.alerts


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    alert = runtime.alerts.acknowledge(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    await runtime.broadcast()
    return alert


@router.get("/analytics/summary")
async def analytics_summary():
    return runtime.live_update().summary


@router.get("/live")
async def live_snapshot():
    return runtime.live_update()

