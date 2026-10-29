import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";

class FakeSocket {
  static instances: FakeSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((ev: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  constructor(readonly url: string) {
    FakeSocket.instances.push(this);
  }
  close() {}
  open() {
    act(() => this.onopen?.());
  }
  drop() {
    act(() => this.onclose?.());
  }
  send(msg: unknown) {
    act(() => this.onmessage?.({ data: JSON.stringify(msg) }));
  }
}

const entity = { src_ip: "10.0.0.5", dst_ip: "10.0.0.9" };
const detection = (id: string, source = "flowsight") => ({
  detection_id: id,
  source,
  flow_id: `flow-${id}`,
  entity,
  ts: "2026-10-21T10:00:00Z",
  score: 0.9,
  label: "dns_tunnel",
  features: {},
  threshold_used: 0.5,
});
const alert = {
  alert_id: "a1",
  entity,
  detection_ids: ["d1", "d2"],
  severity: "high",
  ts: "2026-10-21T10:00:01Z",
  status: "open",
  session_id: null,
};
const record = (over: object = {}) => ({
  replay_id: "r1",
  pcap_name: "dns_tunnel_plus_benign.pcap",
  started: "2026-10-21T10:00:00Z",
  ended: null,
  state: "running",
  error: null,
  flow_count: 0,
  detection_count: 0,
  alert_count: 0,
  ...over,
});

type Backend = {
  replays: object[];
  detections: object[];
  alerts: object[];
  post: () => { status: number; body: object };
  down: boolean;
};

let backend: Backend;
let calls: string[];

function json(status: number, body: object) {
  return Promise.resolve(new Response(JSON.stringify(body), { status }));
}

beforeEach(() => {
  FakeSocket.instances = [];
  calls = [];
  backend = {
    replays: [],
    detections: [],
    alerts: [],
    post: () => ({ status: 200, body: { replay_id: "r1" } }),
    down: false,
  };
  vi.stubGlobal("WebSocket", FakeSocket);
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string, init?: RequestInit) => {
      calls.push(`${init?.method ?? "GET"} ${url}`);
      if (backend.down) return Promise.reject(new TypeError("Failed to fetch"));
      if (url === "/api/pcaps") return json(200, ["dns_tunnel_plus_benign.pcap", "control.pcap"]);
      if (url === "/api/replays") return json(200, backend.replays);
      if (url.startsWith("/api/detections")) return json(200, backend.detections);
      if (url.startsWith("/api/alerts")) return json(200, backend.alerts);
      if (url === "/api/replay") {
        const { status, body } = backend.post();
        return json(status, body);
      }
      return json(404, {});
    }),
  );
});

afterEach(() => vi.unstubAllGlobals());

async function openConsole() {
  render(<App reconnectMs={0} />);
  await screen.findByRole("option", { name: "control.pcap" });
  await waitFor(() => expect(FakeSocket.instances).toHaveLength(1));
  FakeSocket.instances[0].open();
  return FakeSocket.instances[0];
}

const done = (over: object = {}) => ({
  type: "replay_done",
  replay_id: "r1",
  data: { state: "done", error: null, flow_count: 40, detection_count: 2, alert_count: 1, ...over },
});

describe("Console", () => {
  it("starts a replay and shows live Detections, one Alert and the finish counts", async () => {
    const socket = await openConsole();
    await userEvent.click(screen.getByRole("button", { name: "Start replay" }));
    expect(calls).toContain("POST /api/replay");
    await screen.findByText(/Replay r1/);

    socket.send({ type: "detection", replay_id: "r1", data: detection("d1") });
    socket.send({ type: "detection", replay_id: "r1", data: detection("d2", "covertrace") });
    socket.send({ type: "alert", replay_id: "r1", data: alert });
    socket.send(done());

    const detections = screen.getByRole("list", { name: "Detections" });
    expect(within(detections).getAllByRole("listitem")).toHaveLength(2);
    expect(within(screen.getByRole("list", { name: "Alerts" })).getAllByRole("listitem")).toHaveLength(1);
    const counts = screen.getByRole("list", { name: "Replay counts" });
    expect(counts).toHaveTextContent("Flows: 40");
    expect(counts).toHaveTextContent("Detections: 2");
    expect(counts).toHaveTextContent("Alerts: 1");
  });

  it("shows zero Alerts in the counts for the control run", async () => {
    const socket = await openConsole();
    await userEvent.click(screen.getByRole("button", { name: "Start replay" }));
    await screen.findByText(/Replay r1/);
    socket.send({ type: "detection", replay_id: "r1", data: detection("d1") });
    socket.send(done({ flow_count: 30, detection_count: 1, alert_count: 0 }));

    expect(screen.getByRole("list", { name: "Replay counts" })).toHaveTextContent("Alerts: 0");
    expect(screen.getByText("No Alerts yet.")).toBeInTheDocument();
  });

  it("reads REST history mid-replay, then drops live duplicates", async () => {
    backend.replays = [record()];
    backend.detections = [detection("d1")];
    const socket = await openConsole();
    await waitFor(() => expect(screen.getByRole("list", { name: "Detections" }).children).toHaveLength(1));

    socket.send({ type: "detection", replay_id: "r1", data: detection("d1") });
    socket.send({ type: "detection", replay_id: "r1", data: detection("d2") });
    expect(screen.getByRole("list", { name: "Detections" }).children).toHaveLength(2);
  });

  it("reads REST again after a socket reconnect and clears the banner", async () => {
    backend.replays = [record()];
    const socket = await openConsole();
    await waitFor(() => expect(calls.filter((c) => c === "GET /api/replays")).toHaveLength(1));

    backend.detections = [detection("d9")];
    socket.drop();
    expect(await screen.findByRole("status")).toHaveTextContent("Reconnecting");
    await waitFor(() => expect(FakeSocket.instances).toHaveLength(2));
    FakeSocket.instances[1].open();

    await waitFor(() => expect(screen.queryByRole("status")).not.toBeInTheDocument());
    await waitFor(() => expect(calls.filter((c) => c === "GET /api/replays")).toHaveLength(2));
    expect(await screen.findByText(/dns_tunnel score 0.90/)).toBeInTheDocument();
  });

  it("shows the reason when a replay fails", async () => {
    const socket = await openConsole();
    await userEvent.click(screen.getByRole("button", { name: "Start replay" }));
    await screen.findByText(/Replay r1/);
    socket.send(done({ state: "failed", error: "FileNotFoundError: gone.pcap" }));

    expect(await screen.findByText(/Replay failed: FileNotFoundError: gone.pcap/)).toBeInTheDocument();
  });

  it("shows a clear message when the replay is refused as busy", async () => {
    backend.post = () => ({ status: 409, body: { detail: "a replay is already running" } });
    await openConsole();
    await userEvent.click(screen.getByRole("button", { name: "Start replay" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("A replay is already running");
  });

  it("says the backend is down in plain words", async () => {
    backend.down = true;
    render(<App reconnectMs={0} />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Backend is down");
  });
});
