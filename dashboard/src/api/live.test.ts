import { describe, expect, it } from "vitest";
import { applyMessage, emptyFeed, startFeed } from "./live";

describe("startFeed", () => {
  it("keeps a replay that already finished over the socket", () => {
    const done = applyMessage(emptyFeed, {
      type: "replay_done",
      replay_id: "r1",
      data: { state: "done", error: null, flow_count: 1, detection_count: 0, alert_count: 0 },
    });
    const feed = startFeed(done, "r1", "control.pcap");
    expect(feed.replay?.state).toBe("done");
    expect(feed.replay?.counts?.alert_count).toBe(0);
    expect(feed.replay?.pcap).toBe("control.pcap");
  });

  it("starts a new replay as running", () => {
    const feed = startFeed(emptyFeed, "r2", "mix.pcap");
    expect(feed.replay?.state).toBe("running");
  });
});

describe("honeypot messages", () => {
  const alert = {
    alert_id: "r1-alert-0001",
    entity: { src_ip: "10.0.2.20", dst_ip: "10.0.0.53" },
    detection_ids: ["a", "b"],
    severity: "medium" as const,
    ts: "2026-10-20T10:00:00Z",
    status: "open" as const,
    session_id: null,
  };

  it("marks the Alert engaged and keeps its session id", () => {
    let feed = applyMessage(emptyFeed, { type: "alert", replay_id: "r1", data: alert });
    feed = applyMessage(feed, {
      type: "alert_engaged",
      replay_id: "r1",
      data: { alert_id: alert.alert_id, session_id: "s-1" },
    });
    expect(feed.alerts[0].status).toBe("engaged");
    expect(feed.alerts[0].session_id).toBe("s-1");
  });

  it("shows a notice when no session could start", () => {
    const feed = applyMessage(emptyFeed, {
      type: "session_failed",
      replay_id: "r1",
      data: { alert_id: "x", error: "RuntimeError: Docker is not running" },
    });
    expect(feed.notice).toBe("No honeypot session: RuntimeError: Docker is not running");
  });
});
