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
  | { type: "replay_done"; replay_id: string; data: ReplayDone };

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
};

export const emptyFeed: Feed = { replay: null, detections: [], alerts: [] };

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
  };
}

// The single handler for every live message. Unknown types are ignored.
export function applyMessage(feed: Feed, msg: LiveMessage): Feed {
  if (!["detection", "alert", "replay_done"].includes(msg.type)) return feed;
  const base = feed.replay?.id === msg.replay_id ? feed : startFeed(emptyFeed, msg.replay_id, null);
  const replay = base.replay!;
  switch (msg.type) {
    case "detection":
      return { ...base, detections: mergeById(base.detections, [msg.data], detectionId) };
    case "alert":
      return { ...base, alerts: mergeById(base.alerts, [msg.data], alertId) };
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
