import { render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { SessionView } from "./Session";

afterEach(() => vi.unstubAllGlobals());

const session = {
  session_id: "s-1",
  alert_id: "a-1",
  service: "ssh-like",
  started: "2026-10-20T10:00:00Z",
  ended: null,
  mitre: [],
  events: [
    { ts: "2026-10-20T10:00:05Z", type: "command", data: { line: "whoami" } },
    { ts: "2026-10-20T10:00:00Z", type: "connect", data: { attacker_addr: "192.0.2.50" } },
  ],
};

it("shows the attacker address and the events in time order", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(session))));
  render(<SessionView sessionId="s-1" />);
  expect(await screen.findByText(/Attacker address: 192.0.2.50/)).toBeInTheDocument();
  const items = screen.getAllByRole("listitem").map((li) => li.textContent ?? "");
  expect(items[0]).toContain("connect");
  expect(items[1]).toContain("whoami");
  expect(screen.getByText("MITRE tags: no tag")).toBeInTheDocument();
});

it("says so when the session cannot be loaded", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 404 })));
  render(<SessionView sessionId="s-9" />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the session.");
});

it("shows empty state when session has no events", async () => {
  const emptySession = { ...session, events: [] };
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(emptySession))));
  render(<SessionView sessionId="s-empty" />);
  expect(
    await screen.findByText("No events recorded in this session."),
  ).toBeInTheDocument();
  expect(screen.queryByRole("list", { name: "Session events" })).not.toBeInTheDocument();
});

it("shows each MITRE tag with its evidence line", async () => {
  const sessionWithMitre = {
    ...session,
    mitre: [
      {
        technique_id: "T1033",
        name: "System Owner/User Discovery",
        evidence: "whoami",
      },
      {
        technique_id: "T1082",
        name: "System Information Discovery",
        evidence: "uname -a",
      },
    ],
  };
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(sessionWithMitre))));
  render(<SessionView sessionId="s-mitre" />);
  expect(
    await screen.findByText("T1033 System Owner/User Discovery: whoami"),
  ).toBeInTheDocument();
  expect(
    screen.getByText("T1082 System Information Discovery: uname -a"),
  ).toBeInTheDocument();
});

it("appends new session events live in time order", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(session))));
  const { rerender } = render(<SessionView sessionId="s-1" />);
  expect(await screen.findByText(/whoami/)).toBeInTheDocument();

  const newEvent = {
    ts: "2026-10-20T10:00:10Z",
    type: "command",
    data: { line: "cat /etc/passwd" },
  };
  rerender(<SessionView sessionId="s-1" liveEvents={[newEvent]} />);
  expect(await screen.findByText(/cat \/etc\/passwd/)).toBeInTheDocument();

  const items = screen.getAllByRole("listitem").map((li) => li.textContent ?? "");
  expect(items[0]).toContain("connect");
  expect(items[1]).toContain("whoami");
  expect(items[2]).toContain("cat /etc/passwd");
});

it("supports attacker address from src property", async () => {
  const sessionWithSrc = {
    ...session,
    events: [
      { ts: "2026-10-20T10:00:00Z", type: "connect", data: { src: "10.0.0.99" } },
    ],
  };
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(sessionWithSrc))));
  render(<SessionView sessionId="s-src" />);
  expect(await screen.findByText(/Attacker address: 10.0.0.99/)).toBeInTheDocument();
});
