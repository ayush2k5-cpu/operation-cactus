import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Rule } from "./api/client";
import { Rules } from "./Rules";

afterEach(() => vi.unstubAllGlobals());

const proposedRule: Rule = {
  rule_id: "r-1",
  target: "covertrace",
  type: "ioc",
  match: { qname_suffix: ".t.example.test" },
  session_id: "s-100",
  status: "proposed",
};

const activeRule: Rule = {
  rule_id: "r-2",
  target: "covertrace",
  type: "ioc",
  match: { src_ip: "10.0.0.5" },
  session_id: "s-200",
  status: "active",
};

describe("Rules view", () => {
  it("displays rules with status, target, match, and session link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url.startsWith("/api/rules")) {
          return new Response(JSON.stringify([proposedRule, activeRule]));
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<Rules onBack={() => {}} />);
    expect(await screen.findByText(/r-1/)).toBeInTheDocument();
    expect(screen.getByText(/\[proposed\]/)).toBeInTheDocument();
    expect(screen.getAllByText(/target: covertrace/)).toHaveLength(2);
    expect(screen.getByText(/qname_suffix: \.t\.example\.test/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Session s-100" })).toBeInTheDocument();

    expect(screen.getByText(/r-2/)).toBeInTheDocument();
    expect(screen.getByText(/\[active\]/)).toBeInTheDocument();
    expect(screen.getByText(/src_ip: 10\.0\.0\.5/)).toBeInTheDocument();
  });

  it("shows empty state when there are no rules", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify([]))),
    );

    render(<Rules onBack={() => {}} />);
    expect(await screen.findByText("No Rules yet.")).toBeInTheDocument();
  });

  it("shows action buttons only on proposed rules", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify([proposedRule, activeRule]))),
    );

    render(<Rules onBack={() => {}} />);
    await screen.findByText(/r-1/);

    expect(screen.getByRole("button", { name: "Approve" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reject" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Approve" })).toHaveLength(1);
  });

  it("approves a proposed rule and updates the row at once", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push(`${init?.method ?? "GET"} ${url}`);
        if (url === "/api/rules/r-1/approve") {
          return new Response(JSON.stringify({ ...proposedRule, status: "active" }));
        }
        if (url.startsWith("/api/rules")) {
          return new Response(JSON.stringify([proposedRule]));
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<Rules onBack={() => {}} />);
    const approveBtn = await screen.findByRole("button", { name: "Approve" });
    await userEvent.click(approveBtn);

    expect(calls).toContain("POST /api/rules/r-1/approve");
    expect(await screen.findByText(/\[active\]/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reject" })).not.toBeInTheDocument();
  });

  it("rejects a proposed rule and updates the row at once", async () => {
    const calls: string[] = [];
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string, init?: RequestInit) => {
        calls.push(`${init?.method ?? "GET"} ${url}`);
        if (url === "/api/rules/r-1/reject") {
          return new Response(JSON.stringify({ ...proposedRule, status: "rejected" }));
        }
        if (url.startsWith("/api/rules")) {
          return new Response(JSON.stringify([proposedRule]));
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<Rules onBack={() => {}} />);
    const rejectBtn = await screen.findByRole("button", { name: "Reject" });
    await userEvent.click(rejectBtn);

    expect(calls).toContain("POST /api/rules/r-1/reject");
    expect(await screen.findByText(/\[rejected\]/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Approve" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Reject" })).not.toBeInTheDocument();
  });

  it("displays an alert message when an action is refused with 409", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/rules/r-1/approve") {
          return new Response(JSON.stringify({ detail: "rule is already active" }), {
            status: 409,
          });
        }
        if (url.startsWith("/api/rules")) {
          return new Response(JSON.stringify([proposedRule]));
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<Rules onBack={() => {}} />);
    const approveBtn = await screen.findByRole("button", { name: "Approve" });
    await userEvent.click(approveBtn);

    expect(await screen.findByRole("alert")).toHaveTextContent("rule is already active");
  });

  it("toggles inline SessionView when clicking source session link", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string) => {
        if (url === "/api/sessions/s-100") {
          return new Response(
            JSON.stringify({
              session_id: "s-100",
              alert_id: "a-1",
              service: "ssh-like",
              started: "2026-10-20T10:00:00Z",
              ended: null,
              mitre: [],
              events: [
                {
                  ts: "2026-10-20T10:00:00Z",
                  type: "connect",
                  data: { attacker_addr: "192.0.2.50" },
                },
              ],
            }),
          );
        }
        if (url.startsWith("/api/rules")) {
          return new Response(JSON.stringify([proposedRule]));
        }
        return new Response("{}", { status: 404 });
      }),
    );

    render(<Rules onBack={() => {}} />);
    const sessionBtn = await screen.findByRole("button", { name: "Session s-100" });
    await userEvent.click(sessionBtn);

    expect(await screen.findByText(/Attacker address: 192.0.2.50/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hide session s-100" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Hide session s-100" }));
    await waitFor(() =>
      expect(screen.queryByText(/Attacker address: 192.0.2.50/)).not.toBeInTheDocument(),
    );
  });

  it("merges live rules without creating duplicates", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => new Response(JSON.stringify([proposedRule]))),
    );

    const { rerender } = render(<Rules onBack={() => {}} />);
    expect(await screen.findByText(/r-1/)).toBeInTheDocument();
    expect(screen.getByText(/\[proposed\]/)).toBeInTheDocument();

    // Live update for r-1 to active
    rerender(
      <Rules
        onBack={() => {}}
        liveRules={[{ ...proposedRule, status: "active" }]}
      />,
    );

    expect(await screen.findByText(/\[active\]/)).toBeInTheDocument();
    expect(screen.getAllByText(/r-1/)).toHaveLength(1);

    // Live addition of new rule r-3
    const newRule: Rule = {
      rule_id: "r-3",
      target: "covertrace",
      type: "ioc",
      match: { src_ip: "10.0.0.7" },
      session_id: "s-300",
      status: "proposed",
    };

    rerender(
      <Rules
        onBack={() => {}}
        liveRules={[{ ...proposedRule, status: "active" }, newRule]}
      />,
    );

    expect(await screen.findByText(/r-3/)).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
  });
});
