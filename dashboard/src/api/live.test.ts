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
