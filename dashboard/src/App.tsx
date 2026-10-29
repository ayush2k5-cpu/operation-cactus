import { useEffect, useState, type ReactNode } from "react";
import {
  ApiError,
  type Alert,
  type Detection,
  type ReplayRecord,
  closeAlert,
  listAlerts,
  listDetections,
  listPcaps,
  listReplays,
  startReplay,
} from "./api/client";
import { SessionView } from "./Session";
import {
  applyMessage,
  emptyFeed,
  mergeHistory,
  startFeed,
  type Feed,
  type LiveMessage,
  type Replay,
} from "./api/live";
import { Compare } from "./Compare";
import "./styles.css";

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

function closeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 404) return "Alert not found.";
    if (err.status === 409) return "Alert is already closed.";
    return `Could not close the Alert: ${err.message}`;
  }
  return BACKEND_DOWN;
}

function Signal({ running }: { running: boolean }) {
  const spokes = Array.from({ length: 72 }, (_, i) => ({
    angle: i * 5,
    from: 28 + (i % 5) * 6,
    to: 110 + ((i * 37) % 80),
  }));
  return (
    <svg className="signal" data-running={running} viewBox="-200 -200 400 400" aria-hidden="true">
      <defs>
        <linearGradient id="sweep" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#0000f2" stopOpacity="0" />
          <stop offset="1" stopColor="#3a3aff" stopOpacity="0.85" />
        </linearGradient>
      </defs>
      {[60, 110, 160, 195].map((r) => (
        <circle key={r} className="ring" r={r} />
      ))}
      <g className="spokes">
        {spokes.map((sp) => (
          <line key={sp.angle} x1={sp.from} x2={sp.to} transform={`rotate(${sp.angle})`} />
        ))}
      </g>
      <g className="spokes spokes-rev">
        {spokes.filter((_, i) => i % 3 === 0).map((sp) => (
          <line key={sp.angle} x1={sp.from + 20} x2={sp.to + 30} transform={`rotate(${sp.angle + 2})`} />
        ))}
      </g>
      <path className="sweep" d="M0 0 L195 0 A195 195 0 0 0 168.9 -97.5 Z" fill="url(#sweep)" />
      <circle className="blip" cx="90" cy="-70" r="4" />
      <circle className="blip" cx="-120" cy="40" r="4" style={{ animationDelay: "0.8s" }} />
      <circle className="blip" cx="30" cy="140" r="4" style={{ animationDelay: "1.6s" }} />
      <circle className="core" r="6" />
    </svg>
  );
}

type ShellProps = { live?: boolean; running?: boolean; nav?: ReactNode; children: ReactNode };

function Shell({ live, running = false, nav, children }: ShellProps) {
  return (
    <div className="shell">
      <header className="topbar">
        <span className="brand">
          GKMKB
          <br />
          Console
        </span>
        <span className="spacer" />
        {live !== undefined && (
          <span className="tag" data-live={live}>
            {live ? "Live" : "Offline"}
          </span>
        )}
      </header>
      <div className="hero">
        <div className="hero-text">
          <p className="eyebrow">Detection middleware</p>
          <h1>GKMKB Console</h1>
          {nav}
        </div>
        <Signal running={running} />
      </div>
      <main>{children}</main>
    </div>
  );
}

function Counts({ flows, detections, alerts }: { flows: number; detections: number; alerts: number }) {
  return (
    <ul aria-label="Replay counts">
      <li>
        Flows: <b>{flows}</b>
      </li>
      <li>
        Detections: <b>{detections}</b>
      </li>
      <li>
        Alerts: <b>{alerts}</b>
      </li>
    </ul>
  );
}

function isRuleHit(d: Detection): boolean {
  return d.score === 1.0 && d.label.startsWith("rule:");
}

function DetectionItem({ d }: { d: Detection }) {
  const rule = isRuleHit(d);
  const featureEntries = Object.entries(d.features);
  return (
    <li data-rule={rule || undefined} className="detection">
      <span>
        {d.source} {d.label} score {d.score.toFixed(2)} on {d.entity.src_ip} to{" "}
        {d.entity.dst_ip}
      </span>
      {rule && <span> [Rule hit]</span>}
      {d.source === "covertrace" && !rule && <span> [checker: {d.label}]</span>}
      {featureEntries.length > 0 && (
        <ul aria-label="Detection features">
          {featureEntries.map(([k, v]) => (
            <li key={k}>
              {k}: {v}
            </li>
          ))}
        </ul>
      )}
    </li>
  );
}

type AlertRowProps = {
  a: Alert;
  onClose: (id: string) => void;
  closeMsg: string | null;
};

function AlertRow({ a, onClose, closeMsg }: AlertRowProps) {
  const [showSession, setShowSession] = useState(false);
  return (
    <li data-severity={a.severity} className="alert-row" data-status={a.status}>
      {a.severity} Alert on {a.entity.src_ip} to {a.entity.dst_ip} ({a.status})
      {a.status === "open" && (
        <button onClick={() => onClose(a.alert_id)}>Close</button>
      )}
      {a.session_id && (
        <button onClick={() => setShowSession((v) => !v)}>
          {showSession ? "Hide session" : "Open session"}
        </button>
      )}
      {closeMsg && <span role="alert">{closeMsg}</span>}
      {showSession && a.session_id && <SessionView sessionId={a.session_id} />}
    </li>
  );
}

type ReplayDetailProps = {
  record: ReplayRecord;
  onBack: () => void;
  backendDown: boolean;
};

function ReplayDetail({ record, onBack, backendDown }: ReplayDetailProps) {
  const [detections, setDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [closeMsgs, setCloseMsgs] = useState<Record<string, string>>({});

  useEffect(() => {
    if (backendDown) return;
    Promise.all([
      listDetections(record.replay_id),
      listAlerts(record.replay_id),
    ])
      .then(([dets, alts]) => {
        setDetections(dets);
        setAlerts(alts);
        setLoadErr(null);
      })
      .catch(() => setLoadErr(BACKEND_DOWN));
  }, [record.replay_id, backendDown]);

  const handleClose = async (alertId: string) => {
    try {
      await closeAlert(alertId);
      setAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? { ...a, status: "closed" } : a)),
      );
      setCloseMsgs((m) => ({ ...m, [alertId]: "" }));
    } catch (err) {
      setCloseMsgs((m) => ({ ...m, [alertId]: closeError(err) }));
    }
  };

  return (
    <section>
      <button onClick={onBack}>Back to Replays</button>
      <h2>
        Replay {record.replay_id} ({record.pcap_name}): {record.state}
      </h2>
      {record.state !== "running" && (
        <Counts
          flows={record.flow_count}
          detections={record.detection_count}
          alerts={record.alert_count}
        />
      )}
      {loadErr && <p role="alert">{loadErr}</p>}

      <h3>Alerts</h3>
      {alerts.length === 0 && !loadErr && <p>No Alerts for this replay.</p>}
      <ul aria-label="Replay Alerts">
        {alerts.map((a) => (
          <AlertRow
            key={a.alert_id}
            a={a}
            onClose={handleClose}
            closeMsg={closeMsgs[a.alert_id] ?? null}
          />
        ))}
      </ul>

      <h3>Detections</h3>
      {detections.length === 0 && !loadErr && <p>No Detections for this replay.</p>}
      <ul aria-label="Replay Detections">
        {detections.map((d) => (
          <DetectionItem key={d.detection_id} d={d} />
        ))}
      </ul>
    </section>
  );
}

type View =
  | { kind: "live" }
  | { kind: "replays" }
  | { kind: "compare" }
  | { kind: "replay"; record: ReplayRecord };

export function App({ reconnectMs = 1000 }: { reconnectMs?: number }) {
  const [pcaps, setPcaps] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [feed, setFeed] = useState<Feed>(emptyFeed);
  const [error, setError] = useState<string | null>(null);
  const [socketDown, setSocketDown] = useState(false);
  const [view, setView] = useState<View>({ kind: "live" });
  const [replays, setReplays] = useState<ReplayRecord[]>([]);
  const [replaysErr, setReplaysErr] = useState<string | null>(null);
  const [closeMsgs, setCloseMsgs] = useState<Record<string, string>>({});

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

  const handleCloseAlert = async (alertId: string) => {
    try {
      await closeAlert(alertId);
      setFeed((f) => ({
        ...f,
        alerts: f.alerts.map((a) =>
          a.alert_id === alertId ? { ...a, status: "closed" } : a,
        ),
      }));
      setCloseMsgs((m) => ({ ...m, [alertId]: "" }));
    } catch (err) {
      setCloseMsgs((m) => ({ ...m, [alertId]: closeError(err) }));
    }
  };

  const openReplays = () => {
    listReplays()
      .then((recs) => {
        setReplays(recs);
        setReplaysErr(null);
        setView({ kind: "replays" });
      })
      .catch(() => {
        setReplaysErr(BACKEND_DOWN);
        setView({ kind: "replays" });
      });
  };

  const { replay, detections, alerts } = feed;
  const counts = replay?.counts;

  if (view.kind === "replays") {
    return (
      <Shell
        live={!socketDown}
        nav={
          <nav className="tabs">
            <button onClick={() => setView({ kind: "live" })}>Live view</button>
            <button onClick={() => setView({ kind: "compare" })}>Compare thresholds</button>
          </nav>
        }
      >
        <h2>Past Replays</h2>
        {replaysErr && <p role="alert">{replaysErr}</p>}
        {replays.length === 0 && !replaysErr && <p>No past replays.</p>}
        <ul aria-label="Past Replays">
          {replays.map((rec) => (
            <li key={rec.replay_id}>
              <button onClick={() => setView({ kind: "replay", record: rec })}>
                {rec.pcap_name}
              </button>{" "}
              {rec.replay_id} started {rec.started}
              {rec.ended && ` ended ${rec.ended}`} state {rec.state} flows{" "}
              {rec.flow_count} detections {rec.detection_count} alerts{" "}
              {rec.alert_count}
            </li>
          ))}
        </ul>
      </Shell>
    );
  }

  if (view.kind === "compare") {
    return (
      <Shell live={!socketDown}>
        <Compare replays={replays} onBack={() => setView({ kind: "replays" })} />
      </Shell>
    );
  }

  if (view.kind === "replay") {
    return (
      <Shell live={!socketDown}>
        <ReplayDetail
          record={view.record}
          onBack={() => setView({ kind: "replays" })}
          backendDown={!!error}
        />
      </Shell>
    );
  }

  return (
    <Shell
      live={!socketDown}
      running={replay?.state === "running"}
      nav={
        <nav className="tabs">
          <button onClick={openReplays}>Past Replays</button>
        </nav>
      }
    >
      {socketDown && <p role="status">Live feed disconnected. Reconnecting...</p>}
      {error && <p role="alert">{error}</p>}

      <section className="picker">
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
            <Counts
              flows={counts.flow_count}
              detections={counts.detection_count}
              alerts={counts.alert_count}
            />
          )}
        </section>
      )}

      {feed.notice && <p role="status">{feed.notice}</p>}

      <section>
        <h2>Alerts</h2>
        {alerts.length === 0 && <p>No Alerts yet.</p>}
        <ul aria-label="Alerts">
          {alerts.map((a) => (
            <AlertRow
              key={a.alert_id}
              a={a}
              onClose={handleCloseAlert}
              closeMsg={closeMsgs[a.alert_id] ?? null}
            />
          ))}
        </ul>
      </section>

      <section>
        <h2>Detections</h2>
        {detections.length === 0 && <p>No Detections yet.</p>}
        <ul aria-label="Detections">
          {detections.map((d) => (
            <DetectionItem key={d.detection_id} d={d} />
          ))}
        </ul>
      </section>
    </Shell>
  );
}
