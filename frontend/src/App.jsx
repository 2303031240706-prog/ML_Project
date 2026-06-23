import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Camera,
  CheckCircle2,
  Filter,
  Play,
  RadioTower,
  ScanFace,
  ShieldAlert,
  Square,
  TrendingUp,
  UserCheck,
  UserX,
} from "lucide-react";
import { acknowledgeAlert, connectLiveUpdates, fetchLiveSnapshot } from "./services/api.js";

const emptyState = {
  cameras: [],
  alerts: [],
  summary: {
    total_cameras: 0,
    online_cameras: 0,
    active_alerts: 0,
    total_people_count: 0,
    average_risk_score: 0,
    highest_risk_camera: null,
    density_distribution: {},
  },
};

function levelClass(level) {
  return String(level || "Safe").toLowerCase();
}

function Metric({ icon: Icon, label, value }) {
  return (
    <div className="metric">
      <Icon size={18} />
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}

function CameraPanel({ camera }) {
  const hottestZone = useMemo(() => {
    return [...(camera.zones || [])].sort((a, b) => b.density_ratio - a.density_ratio)[0];
  }, [camera.zones]);

  return (
    <article className="camera-panel">
      <div className="camera-feed">
        <div className="scanline" />
        <Camera size={34} />
        <span>{camera.name}</span>
      </div>
      <div className="panel-header">
        <div>
          <h2>{camera.name}</h2>
          <p>{camera.source}</p>
        </div>
        <span className={`badge ${levelClass(camera.density_level)}`}>{camera.density_level}</span>
      </div>
      <div className="camera-stats">
        <div>
          <span>People</span>
          <strong>{camera.people_count}</strong>
        </div>
        <div>
          <span>Risk</span>
          <strong>{camera.risk_score}%</strong>
        </div>
        <div>
          <span>Predicted</span>
          <strong>{camera.predicted_people_count}</strong>
        </div>
      </div>
      <div className="density-bar">
        <span style={{ width: `${Math.min(camera.density_ratio * 100, 100)}%` }} />
      </div>
      <div className="zone-grid">
        {(camera.zones || []).map((zone) => (
          <div key={zone.zone_id} className={`zone ${levelClass(zone.density_level)}`}>
            <span>{zone.name}</span>
            <strong>{zone.people_count}</strong>
          </div>
        ))}
      </div>
      <p className="hotspot">
        Hotspot: {hottestZone?.name || "None"} | Prediction: {camera.prediction_level}
      </p>
    </article>
  );
}

function DeviceCameraPanel() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const previousFrameRef = useRef(null);
  const detectorRef = useRef(null);
  const [cameraState, setCameraState] = useState("idle");
  const [detection, setDetection] = useState({
    count: 0,
    confidence: 0,
    mode: "Waiting",
    message: "Start camera to scan for people",
  });

  useEffect(() => {
    return () => stopCamera(false);
  }, []);

  async function startCamera() {
    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraState("blocked");
      setDetection({
        count: 0,
        confidence: 0,
        mode: "Unavailable",
        message: "This browser does not expose camera access.",
      });
      return;
    }

    try {
      setCameraState("starting");
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      });
      streamRef.current = stream;
      videoRef.current.srcObject = stream;
      await videoRef.current.play();

      if ("FaceDetector" in window) {
        detectorRef.current = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 8 });
      }

      setCameraState("running");
      scanFrame();
    } catch (error) {
      setCameraState("blocked");
      setDetection({
        count: 0,
        confidence: 0,
        mode: "Permission needed",
        message: "Allow camera access in the browser prompt, then try again.",
      });
    }
  }

  function stopCamera(updateState = true) {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    previousFrameRef.current = null;
    if (updateState) {
      setCameraState("idle");
    }
  }

  async function scanFrame() {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { willReadFrequently: true });

    if (!video || !canvas || !context || !streamRef.current) {
      return;
    }

    if (video.videoWidth && video.videoHeight) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      if (detectorRef.current) {
        try {
          const faces = await detectorRef.current.detect(video);
          drawDetections(context, faces);
          setDetection({
            count: faces.length,
            confidence: faces.length ? 96 : 0,
            mode: "Face detector",
            message: faces.length ? "Human presence detected" : "No person detected",
          });
        } catch (error) {
          detectorRef.current = null;
        }
      }

      if (!detectorRef.current) {
        const motionScore = detectMotion(context, canvas.width, canvas.height);
        const found = motionScore > 11;
        setDetection({
          count: found ? 1 : 0,
          confidence: Math.min(Math.round(motionScore * 5), 92),
          mode: "Motion fallback",
          message: found ? "Possible person movement detected" : "No person detected",
        });
      }
    }

    window.setTimeout(scanFrame, 500);
  }

  function drawDetections(context, faces) {
    context.lineWidth = 4;
    context.strokeStyle = "#45d6a7";
    context.fillStyle = "rgba(69, 214, 167, 0.16)";
    faces.forEach((face) => {
      const box = face.boundingBox;
      context.fillRect(box.x, box.y, box.width, box.height);
      context.strokeRect(box.x, box.y, box.width, box.height);
    });
  }

  function detectMotion(context, width, height) {
    const sampleWidth = 80;
    const sampleHeight = Math.max(45, Math.round((height / width) * sampleWidth));
    const scratch = document.createElement("canvas");
    scratch.width = sampleWidth;
    scratch.height = sampleHeight;
    const scratchContext = scratch.getContext("2d", { willReadFrequently: true });
    scratchContext.drawImage(context.canvas, 0, 0, sampleWidth, sampleHeight);
    const current = scratchContext.getImageData(0, 0, sampleWidth, sampleHeight).data;
    const previous = previousFrameRef.current;
    previousFrameRef.current = current;

    if (!previous) {
      return 0;
    }

    let changed = 0;
    for (let index = 0; index < current.length; index += 16) {
      const delta =
        Math.abs(current[index] - previous[index]) +
        Math.abs(current[index + 1] - previous[index + 1]) +
        Math.abs(current[index + 2] - previous[index + 2]);
      if (delta > 58) {
        changed += 1;
      }
    }
    return (changed / (current.length / 16)) * 100;
  }

  const isRunning = cameraState === "running";
  const DetectionIcon = detection.count > 0 ? UserCheck : UserX;

  return (
    <article className="camera-panel device-panel">
      <div className="device-feed">
        <video ref={videoRef} muted playsInline />
        <canvas ref={canvasRef} />
        {!isRunning && (
          <div className="camera-placeholder">
            <ScanFace size={38} />
            <span>Device Camera</span>
          </div>
        )}
      </div>
      <div className="panel-header">
        <div>
          <h2>Device Camera</h2>
          <p>{detection.mode}</p>
        </div>
        <span className={`badge ${detection.count > 0 ? "warning" : "safe"}`}>
          <DetectionIcon size={14} />
          {detection.count > 0 ? "Human" : "Clear"}
        </span>
      </div>
      <div className="camera-stats">
        <div>
          <span>Detected</span>
          <strong>{detection.count}</strong>
        </div>
        <div>
          <span>Confidence</span>
          <strong>{detection.confidence}%</strong>
        </div>
        <div>
          <span>Status</span>
          <strong>{isRunning ? "Live" : cameraState}</strong>
        </div>
      </div>
      <div className="camera-actions">
        <button className="action-button primary" onClick={startCamera} disabled={cameraState === "starting"} type="button">
          <Play size={16} />
          {cameraState === "starting" ? "Starting" : "Start Camera"}
        </button>
        <button className="action-button" onClick={stopCamera} disabled={!streamRef.current} type="button">
          <Square size={16} />
          Stop
        </button>
      </div>
      <p className="hotspot">{detection.message}</p>
    </article>
  );
}

function OperationsStrip({ summary }) {
  const distribution = summary.density_distribution || {};
  const levels = ["Safe", "Warning", "Danger", "Critical"];

  return (
    <section className="operations-strip">
      <div className="ops-main">
        <TrendingUp size={18} />
        <div>
          <span>Average Risk</span>
          <strong>{summary.average_risk_score ?? 0}%</strong>
        </div>
      </div>
      <div className="density-mix">
        {levels.map((level) => (
          <span key={level} className={levelClass(level)}>
            {level} <strong>{distribution[level] || 0}</strong>
          </span>
        ))}
      </div>
    </section>
  );
}

function Alerts({ alerts, onAcknowledge }) {
  const [filter, setFilter] = useState("all");
  const visibleAlerts = alerts.filter((alert) => filter === "all" || alert.status === filter);

  return (
    <section className="alerts">
      <div className="section-title">
        <ShieldAlert size={19} />
        <h2>Live Alerts</h2>
      </div>
      <div className="alert-toolbar" aria-label="Alert filters">
        <Filter size={15} />
        {["all", "active", "acknowledged"].map((item) => (
          <button
            key={item}
            className={filter === item ? "selected" : ""}
            onClick={() => setFilter(item)}
            type="button"
          >
            {item}
          </button>
        ))}
      </div>
      <div className="alert-list">
        {visibleAlerts.length === 0 && <p className="muted">No alerts match this filter.</p>}
        {visibleAlerts.map((alert) => (
          <article key={alert.alert_id} className={`alert ${levelClass(alert.level)}`}>
            <div>
              <strong>{alert.title}</strong>
              <p>{alert.message}</p>
              <span>{alert.recommended_action}</span>
            </div>
            {alert.status === "active" ? (
              <button onClick={() => onAcknowledge(alert.alert_id)}>Acknowledge</button>
            ) : (
              <small>{alert.status}</small>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

export default function App() {
  const [data, setData] = useState(emptyState);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let active = true;
    const refreshSnapshot = () => {
      fetchLiveSnapshot()
        .then((payload) => {
          if (!active) {
            return;
          }
          setData(payload);
          setConnected(true);
        })
        .catch(() => {
          if (active) {
            setConnected(false);
          }
        });
    };

    refreshSnapshot();
    const refreshTimer = window.setInterval(refreshSnapshot, 5000);
    const socket = connectLiveUpdates((payload) => {
      setConnected(true);
      setData(payload);
    });
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    return () => {
      active = false;
      window.clearInterval(refreshTimer);
      socket.close();
    };
  }, []);

  async function handleAcknowledge(alertId) {
    await acknowledgeAlert(alertId);
    const payload = await fetchLiveSnapshot();
    setData(payload);
  }

  return (
    <main>
      <header className="topbar">
        <div>
          <h1>Smart Crowd Safety System</h1>
          <p>Real-time density monitoring, surge prediction, and public safety alerts</p>
        </div>
        <span className={`connection ${connected ? "online" : "offline"}`}>
          <RadioTower size={16} />
          {connected ? "Live" : "Connecting"}
        </span>
      </header>

      <section className="metrics">
        <Metric icon={Camera} label="Cameras" value={`${data.summary.online_cameras}/${data.summary.total_cameras}`} />
        <Metric icon={Activity} label="People Count" value={data.summary.total_people_count} />
        <Metric icon={AlertTriangle} label="Active Alerts" value={data.summary.active_alerts} />
        <Metric icon={CheckCircle2} label="Highest Risk" value={data.summary.highest_risk_camera || "None"} />
      </section>

      <OperationsStrip summary={data.summary} />

      <section className="workspace">
        <div className="camera-grid">
          <DeviceCameraPanel />
          {data.cameras.map((camera) => (
            <CameraPanel key={camera.camera_id} camera={camera} />
          ))}
        </div>
        <Alerts alerts={data.alerts} onAcknowledge={handleAcknowledge} />
      </section>
    </main>
  );
}
