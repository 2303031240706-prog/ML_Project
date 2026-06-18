# AI-Powered Smart Crowd Density Monitoring and Public Safety Alert System

Production-style starter project for real-time crowd monitoring, person detection, density estimation, overcrowding prediction, alert escalation, privacy protection, and control-room dashboards.

The project runs in simulation mode by default, so you can start the API and dashboard before adding CCTV/IP camera streams or GPU inference.

## Features

- Real-time multi-camera monitoring
- YOLOv8-ready person detection pipeline
- ByteTrack/DeepSORT-ready object tracking abstraction
- Zone-based density classification: Safe, Warning, Danger, Critical
- Hotspot detection and heatmap-ready zone metrics
- Crowd surge prediction service using recent trends
- Abnormal behavior detection heuristics for sudden gathering and panic movement
- Alert escalation workflow for control room operations
- Face blurring hook for privacy protection
- Incident snapshot/video metadata model
- WebSocket live updates for dashboard clients
- MongoDB/Redis-ready architecture with in-memory fallback
- Docker Compose deployment skeleton

## Project Structure

```text
smart-crowd-safety-system/
  backend/
    app/
      api/              FastAPI routes and WebSocket endpoints
      core/             settings, app state, startup wiring
      cv/               detection, tracking, zones, privacy modules
      models/           Pydantic schemas
      services/         camera loop, alerts, predictions, analytics
      storage/          in-memory and MongoDB repository adapters
      main.py           FastAPI entrypoint
    tests/
    requirements.txt
    .env.example
  frontend/
    src/
      components/
      services/
      App.jsx
      main.jsx
    package.json
  docker-compose.yml
```

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

For real YOLOv8 inference and OpenCV frame processing, install the optional AI dependencies:

```bash
pip install -r requirements-ai.txt
```

For MongoDB and Redis client libraries:

```bash
pip install -r requirements-storage.txt
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard: http://localhost:5173

## Real Camera Setup

Edit `backend/.env`:

```env
SIMULATION_MODE=false
CAMERA_SOURCES=Main Gate|rtsp://user:pass@camera-ip/stream,Platform 1|rtsp://user:pass@camera-ip/stream2
```

The current implementation is designed to degrade gracefully:

- If `ultralytics` is installed and `YOLO_MODEL_PATH` is valid, YOLOv8 inference is used.
- If real camera streams fail or simulation mode is enabled, synthetic camera telemetry is generated.
- Tracking uses a simple IoU tracker by default and can be replaced with ByteTrack/DeepSORT.

## API Summary

- `GET /health`
- `GET /api/cameras`
- `GET /api/alerts`
- `POST /api/alerts/{alert_id}/acknowledge`
- `GET /api/analytics/summary`
- `WS /ws/live`

## Notes for AI/ML Internships

This codebase is intentionally modular. You can show:

- YOLOv8 person detection integration
- Object tracking to avoid duplicate counts
- Density estimation and alert thresholds
- Forecasting service for proactive intervention
- Real-time dashboard over WebSockets
- Smart city deployment pattern using FastAPI, React, MongoDB, Redis, and Docker
