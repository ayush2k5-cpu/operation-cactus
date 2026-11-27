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

  it("appends live session events for a session", () => {
    const event = { ts: "2026-10-20T10:00:00Z", type: "connect", data: { attacker_addr: "192.0.2.50" } };
    const feed = applyMessage(emptyFeed, {
      type: "session_event",
      session_id: "s-1",
      data: event,
    });
    expect(feed.sessionEvents["s-1"]).toEqual([event]);
  });

  it("adds and updates live rules without duplicates", () => {
    const rule1 = {
      rule_id: "r-1",
      target: "covertrace" as const,
      type: "ioc" as const,
      match: { qname_suffix: ".t.example.test" },
      session_id: "s-1",
      status: "proposed" as const,
    };
    let feed = applyMessage(emptyFeed, { type: "rule", data: rule1 });
    expect(feed.rules).toEqual([rule1]);

    const rule1Approved = { ...rule1, status: "active" as const };
    feed = applyMessage(feed, { type: "rule", data: rule1Approved });
    expect(feed.rules).toHaveLength(1);
    expect(feed.rules[0].status).toBe("active");

    const rule2 = {
      rule_id: "r-2",
      target: "covertrace" as const,
      type: "ioc" as const,
      match: { src_ip: "10.0.0.5" },
      session_id: "s-2",
      status: "proposed" as const,
    };
    feed = applyMessage(feed, { type: "rule", data: rule2 });
    expect(feed.rules).toHaveLength(2);
    expect(feed.rules[1].rule_id).toBe("r-2");
  });
});
