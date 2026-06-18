const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const WS_BASE = API_BASE.replace("http", "ws");

export async function fetchLiveSnapshot() {
  const response = await fetch(`${API_BASE}/api/live`);
  if (!response.ok) {
    throw new Error("Unable to fetch live snapshot");
  }
  return response.json();
}

export async function acknowledgeAlert(alertId) {
  const response = await fetch(`${API_BASE}/api/alerts/${alertId}/acknowledge`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error("Unable to acknowledge alert");
  }
  return response.json();
}

export function connectLiveUpdates(onMessage) {
  const socket = new WebSocket(`${WS_BASE}/ws/live`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return socket;
}

