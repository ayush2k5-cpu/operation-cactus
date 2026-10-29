import type { components } from "./schema";

export type Detection = components["schemas"]["Detection"];
export type Alert = components["schemas"]["Alert"];
export type ReplayRecord = components["schemas"]["ReplayRecord"];

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }
  return res.json();
}

export const listPcaps = () => request<string[]>("/api/pcaps");
export const listReplays = () => request<ReplayRecord[]>("/api/replays");
export const listDetections = (replayId: string) =>
  request<Detection[]>(`/api/detections?replay_id=${replayId}&limit=500`);
export const listAlerts = (replayId: string) =>
  request<Alert[]>(`/api/alerts?replay_id=${replayId}&limit=500`);
export const startReplay = (pcap: string) =>
  request<{ replay_id: string }>("/api/replay", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pcap }),
  });
