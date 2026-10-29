import type { Alert, Detection } from "./client";

export type ReplayDone = {
  state: "done" | "failed";
  error: string | null;
  flow_count: number;
  detection_count: number;
  alert_count: number;
};

export type LiveMessage =
  | { type: "detection"; replay_id: string; data: Detection }
  | { type: "alert"; replay_id: string; data: Alert }
  | { type: "replay_done"; replay_id: string; data: ReplayDone }
  | { type: "alert_engaged"; replay_id: string; data: { alert_id: string; session_id: string } }
  | { type: "session_failed"; replay_id: string; data: { alert_id: string; error: string } };

export type Replay = {
  id: string;
  pcap: string | null;
  state: "running" | "done" | "failed";
  error: string | null;
  counts: Pick<ReplayDone, "flow_count" | "detection_count" | "alert_count"> | null;
};

export type Feed = {
  replay: Replay | null;
  detections: Detection[];
  alerts: Alert[];
  notice: string | null;
};

export const emptyFeed: Feed = { replay: null, detections: [], alerts: [], notice: null };

function mergeById<T>(items: T[], incoming: T[], id: (item: T) => string): T[] {
  const seen = new Set(items.map(id));
  return [...items, ...incoming.filter((item) => !seen.has(id(item)) && seen.add(id(item)))];
}

const detectionId = (d: Detection) => d.detection_id;
const alertId = (a: Alert) => a.alert_id;

export function mergeHistory(
  feed: Feed,
  replay: Replay,
  detections: Detection[],
  alerts: Alert[],
): Feed {
  const same = feed.replay?.id === replay.id;
  const finished = same && feed.replay?.state !== "running";
  return {
    replay: finished ? feed.replay : replay,
    detections: mergeById(same ? feed.detections : [], detections, detectionId),
    alerts: mergeById(same ? feed.alerts : [], alerts, alertId),
    notice: same ? feed.notice : null,
  };
}

export function startFeed(feed: Feed, id: string, pcap: string | null): Feed {
  const same = feed.replay?.id === id;
  // A fast replay can finish over the socket before the start request returns.
  if (same && feed.replay) return { ...feed, replay: { ...feed.replay, pcap } };
  return {
    replay: { id, pcap, state: "running", error: null, counts: null },
    detections: same ? feed.detections : [],
    alerts: same ? feed.alerts : [],
    notice: same ? feed.notice : null,
  };
}

// The single handler for every live message. Unknown types are ignored.
export function applyMessage(feed: Feed, msg: LiveMessage): Feed {
  const known = ["detection", "alert", "replay_done", "alert_engaged", "session_failed"];
  if (!known.includes(msg.type)) return feed;
  const base = feed.replay?.id === msg.replay_id ? feed : startFeed(emptyFeed, msg.replay_id, null);
  const replay = base.replay!;
  switch (msg.type) {
    case "detection":
      return { ...base, detections: mergeById(base.detections, [msg.data], detectionId) };
    case "alert":
      return { ...base, alerts: mergeById(base.alerts, [msg.data], alertId) };
    case "alert_engaged":
      return {
        ...base,
        alerts: base.alerts.map((a) =>
          a.alert_id === msg.data.alert_id
            ? { ...a, status: a.status === "open" ? "engaged" : a.status, session_id: msg.data.session_id }
            : a,
        ),
      };
    case "session_failed":
      return { ...base, notice: `No honeypot session: ${msg.data.error}` };
    case "replay_done":
      return {
        ...base,
        replay: {
          ...replay,
          state: msg.data.state,
          error: msg.data.error,
          counts: {
            flow_count: msg.data.flow_count,
            detection_count: msg.data.detection_count,
            alert_count: msg.data.alert_count,
          },
        },
      };
  }
}
