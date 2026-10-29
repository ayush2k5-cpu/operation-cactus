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
  expect(screen.getByText("MITRE tags: none yet")).toBeInTheDocument();
});

it("says so when the session cannot be loaded", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => new Response("{}", { status: 404 })));
  render(<SessionView sessionId="s-9" />);
  expect(await screen.findByRole("alert")).toHaveTextContent("Could not load the session.");
});
