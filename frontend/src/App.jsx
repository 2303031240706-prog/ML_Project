import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Camera, CheckCircle2, RadioTower, ShieldAlert } from "lucide-react";
import { acknowledgeAlert, connectLiveUpdates, fetchLiveSnapshot } from "./services/api.js";

const emptyState = {
  cameras: [],
  alerts: [],
  summary: {
    total_cameras: 0,
    online_cameras: 0,
    active_alerts: 0,
    total_people_count: 0,
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
        Hotspot: {hottestZone?.name || "None"} · Prediction: {camera.prediction_level}
      </p>
    </article>
  );
}

function Alerts({ alerts, onAcknowledge }) {
  return (
    <section className="alerts">
      <div className="section-title">
        <ShieldAlert size={19} />
        <h2>Live Alerts</h2>
      </div>
      <div className="alert-list">
        {alerts.length === 0 && <p className="muted">No alerts yet. Monitoring is active.</p>}
        {alerts.map((alert) => (
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
    fetchLiveSnapshot().then(setData).catch(() => undefined);
    const socket = connectLiveUpdates((payload) => {
      setConnected(true);
      setData(payload);
    });
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    return () => socket.close();
  }, []);

  async function handleAcknowledge(alertId) {
    await acknowledgeAlert(alertId);
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

      <section className="workspace">
        <div className="camera-grid">
          {data.cameras.map((camera) => (
            <CameraPanel key={camera.camera_id} camera={camera} />
          ))}
        </div>
        <Alerts alerts={data.alerts} onAcknowledge={handleAcknowledge} />
      </section>
    </main>
  );
}

