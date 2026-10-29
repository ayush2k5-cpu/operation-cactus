import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

class FakeSocket {
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  close() {}
}

const entity = { src_ip: "10.0.0.5", dst_ip: "10.0.0.9" };
const detection = (id: string, over: object = {}) => ({
  detection_id: id,
  source: "covertrace",
  flow_id: `flow-${id}`,
  entity,
  ts: "2026-10-21T10:00:00Z",
  score: 0.9,
  label: "dns_entropy",
  features: {},
  threshold_used: 0.5,
  ...over,
});
const record = (id: string, pcap: string) => ({
  replay_id: id,
  pcap_name: pcap,
  started: "2026-10-21T10:00:00Z",
  ended: "2026-10-21T10:05:00Z",
  state: "done",
  error: null,
  flow_count: 40,
  detection_count: 1,
  alert_count: 0,
});

let byReplay: Record<string, object[]>;

function json(body: object) {
  return Promise.resolve(new Response(JSON.stringify(body), { status: 200 }));
}

beforeEach(() => {
  byReplay = {
    r1: [detection("d1", { threshold_used: 0.4, score: 0.8 })],
    r2: [detection("d2", { threshold_used: 0.7, score: 0.75 })],
    r3: [detection("d3", { source: "flowsight", label: "dns_tunnel" })],
  };
  vi.stubGlobal("WebSocket", FakeSocket);
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url === "/api/pcaps") return json(["a.pcap"]);
      if (url === "/api/replays")
        return json([record("r1", "a.pcap"), record("r2", "a.pcap"), record("r3", "b.pcap")]);
      const m = url.match(/^\/api\/detections\?replay_id=(\w+)/);
      if (m) return json(byReplay[m[1]] ?? []);
      return json([]);
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());

async function openCompare() {
  render(<App reconnectMs={0} />);
  await userEvent.click(await screen.findByRole("button", { name: "Past Replays" }));
  await userEvent.click(await screen.findByRole("button", { name: "Compare thresholds" }));
  await screen.findByText(/from Detections/);
}

async function pick(label: string, id: string) {
  await userEvent.selectOptions(screen.getByLabelText(label), id);
}

describe("Threshold compare", () => {
  it("shows two replays with two different thresholds and scores", async () => {
    await openCompare();
    await pick("First replay", "r1");
    await pick("Second replay", "r2");

    const first = await screen.findByRole("region", { name: "Replay r1" });
    const second = await screen.findByRole("region", { name: "Replay r2" });
    expect(within(first).getByRole("cell", { name: "0.4" })).toBeInTheDocument();
    expect(within(first).getByRole("cell", { name: "0.80" })).toBeInTheDocument();
    expect(within(second).getByRole("cell", { name: "0.7" })).toBeInTheDocument();
    expect(within(second).getByRole("cell", { name: "0.75" })).toBeInTheDocument();
  });

  it("is labelled from Detections and never says Baseline", async () => {
    await openCompare();
    await pick("First replay", "r1");
    await pick("Second replay", "r2");
    await screen.findByRole("region", { name: "Replay r2" });

    expect(screen.getByRole("heading", { name: /from Detections/ })).toBeInTheDocument();
    expect(document.body).not.toHaveTextContent(/baseline/i);
  });

  it("says there is no threshold for a replay with no CoverTrace Detection", async () => {
    await openCompare();
    await pick("First replay", "r1");
    await pick("Second replay", "r3");

    const empty = await screen.findByRole("region", { name: "Replay r3" });
    expect(empty).toHaveTextContent("no Detection, so no threshold shown");
    expect(within(empty).queryByRole("table")).not.toBeInTheDocument();
  });
});
