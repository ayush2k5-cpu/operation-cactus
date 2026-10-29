import { useEffect, useState } from "react";
import {
  ApiError,
  type Alert,
  type Detection,
  listAlerts,
  listDetections,
  listPcaps,
  listReplays,
  startReplay,
  type ReplayRecord,
} from "./api/client";
import {
  applyMessage,
  emptyFeed,
  mergeHistory,
  startFeed,
  type Feed,
  type LiveMessage,
  type Replay,
} from "./api/live";

const BACKEND_DOWN = "Backend is down. Start the backend and try again.";
const BUSY = "A replay is already running. Wait for it to finish, then start again.";

function toReplay(rec: ReplayRecord): Replay {
  return {
    id: rec.replay_id,
    pcap: rec.pcap_name,
    state: rec.state,
    error: rec.error ?? null,
    counts:
      rec.state === "running"
        ? null
        : {
            flow_count: rec.flow_count,
            detection_count: rec.detection_count,
            alert_count: rec.alert_count,
          },
  };
}

// The running replay, else the newest one, with its Detections and Alerts.
async function readHistory(): Promise<[Replay, Detection[], Alert[]] | null> {
  const replays = await listReplays();
  const rec = replays.find((r) => r.state === "running") ?? replays[0];
  if (!rec) return null;
  const [detections, alerts] = await Promise.all([
    listDetections(rec.replay_id),
    listAlerts(rec.replay_id),
  ]);
  return [toReplay(rec), detections, alerts];
}

function startError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.status === 409 ? BUSY : `Could not start the replay: ${err.message}`;
  }
  return BACKEND_DOWN;
}

export function App({ reconnectMs = 1000 }: { reconnectMs?: number }) {
  const [pcaps, setPcaps] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [feed, setFeed] = useState<Feed>(emptyFeed);
  const [error, setError] = useState<string | null>(null);
  const [socketDown, setSocketDown] = useState(false);

  useEffect(() => {
    const sync = () =>
      readHistory()
        .then((history) => {
          if (history) setFeed((f) => mergeHistory(f, ...history));
          setError(null);
        })
        .catch(() => setError(BACKEND_DOWN));

    let closed = false;
    let socket: WebSocket | undefined;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const connect = (reconnect: boolean) => {
      const scheme = location.protocol === "https:" ? "wss" : "ws";
      socket = new WebSocket(`${scheme}://${location.host}/ws/events`);
      socket.onopen = () => {
        setSocketDown(false);
        if (reconnect) void sync();
      };
      socket.onmessage = (ev) => {
        const msg = JSON.parse(ev.data) as LiveMessage;
        setFeed((f) => applyMessage(f, msg));
      };
      socket.onclose = () => {
        if (closed) return;
        setSocketDown(true);
        timer = setTimeout(() => connect(true), reconnectMs);
      };
    };

    listPcaps()
      .then((names) => {
        setPcaps(names);
        setSelected((s) => s || names[0] || "");
      })
      .catch(() => setError(BACKEND_DOWN));
    void sync().then(() => {
      if (!closed) connect(false);
    });

    return () => {
      closed = true;
      clearTimeout(timer);
      socket?.close();
    };
  }, [reconnectMs]);

  const start = async () => {
    try {
      const { replay_id } = await startReplay(selected);
      setError(null);
      setFeed((f) => startFeed(f, replay_id, selected));
    } catch (err) {
      setError(startError(err));
    }
  };

  const { replay, detections, alerts } = feed;
  const counts = replay?.counts;

  return (
    <main>
      <h1>GKMKB Console</h1>
      {socketDown && <p role="status">Live feed disconnected. Reconnecting...</p>}
      {error && <p role="alert">{error}</p>}

      <section>
        <label>
          Pcap
          <select value={selected} onChange={(e) => setSelected(e.target.value)}>
            {pcaps.map((name) => (
              <option key={name}>{name}</option>
            ))}
          </select>
        </label>
        <button onClick={start} disabled={!selected || replay?.state === "running"}>
          Start replay
        </button>
        {pcaps.length === 0 && <p>No pcaps found in the data folder.</p>}
      </section>

      {replay && (
        <section>
          <h2>
            Replay {replay.id} {replay.pcap && `(${replay.pcap})`}: {replay.state}
          </h2>
          {replay.state === "failed" && <p role="alert">Replay failed: {replay.error}</p>}
          {counts && (
            <ul aria-label="Replay counts">
              <li>Flows: {counts.flow_count}</li>
              <li>Detections: {counts.detection_count}</li>
              <li>Alerts: {counts.alert_count}</li>
            </ul>
          )}
        </section>
      )}

      <section>
        <h2>Alerts</h2>
        {alerts.length === 0 && <p>No Alerts yet.</p>}
        <ul aria-label="Alerts">
          {alerts.map((a) => (
            <li key={a.alert_id}>
              {a.severity} Alert on {a.entity.src_ip} to {a.entity.dst_ip} ({a.status})
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2>Detections</h2>
        {detections.length === 0 && <p>No Detections yet.</p>}
        <ul aria-label="Detections">
          {detections.map((d) => (
            <li key={d.detection_id}>
              {d.source} {d.label} score {d.score.toFixed(2)} on {d.entity.src_ip} to{" "}
              {d.entity.dst_ip}
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
