import { useEffect, useState } from "react";
import { type Rule, ApiError, approveRule, listRules, rejectRule } from "./api/client";
import { SessionView } from "./Session";

export function Rules({
  liveRules = [],
  onBack,
  backendDown,
}: {
  liveRules?: Rule[];
  onBack: () => void;
  backendDown?: boolean;
}) {
  const [rules, setRules] = useState<Rule[]>([]);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [actionMsgs, setActionMsgs] = useState<Record<string, string>>({});
  const [openSessions, setOpenSessions] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (backendDown) return;
    listRules()
      .then((data) => {
        setRules(data);
        setLoadErr(null);
      })
      .catch(() => setLoadErr("Could not load Rules."));
  }, [backendDown]);

  useEffect(() => {
    if (!liveRules || liveRules.length === 0) return;
    setRules((prev) => {
      const copy = [...prev];
      for (const liveRule of liveRules) {
        const idx = copy.findIndex((r) => r.rule_id === liveRule.rule_id);
        if (idx >= 0) {
          copy[idx] = liveRule;
        } else {
          copy.push(liveRule);
        }
      }
      return copy;
    });
  }, [liveRules]);

  const handleApprove = async (ruleId: string) => {
    try {
      const updated = await approveRule(ruleId);
      setRules((prev) => prev.map((r) => (r.rule_id === ruleId ? updated : r)));
      setActionMsgs((m) => ({ ...m, [ruleId]: "" }));
    } catch (err) {
      if (err instanceof ApiError) {
        setActionMsgs((m) => ({ ...m, [ruleId]: err.message }));
      } else {
        setActionMsgs((m) => ({ ...m, [ruleId]: "Could not approve rule." }));
      }
    }
  };

  const handleReject = async (ruleId: string) => {
    try {
      const updated = await rejectRule(ruleId);
      setRules((prev) => prev.map((r) => (r.rule_id === ruleId ? updated : r)));
      setActionMsgs((m) => ({ ...m, [ruleId]: "" }));
    } catch (err) {
      if (err instanceof ApiError) {
        setActionMsgs((m) => ({ ...m, [ruleId]: err.message }));
      } else {
        setActionMsgs((m) => ({ ...m, [ruleId]: "Could not reject rule." }));
      }
    }
  };

  const toggleSession = (ruleId: string) => {
    setOpenSessions((prev) => ({ ...prev, [ruleId]: !prev[ruleId] }));
  };

  return (
    <section aria-label="Rules View">
      <button onClick={onBack}>Back to live feed</button>
      <h2>Detection Rules</h2>
      {loadErr && <p role="alert">{loadErr}</p>}
      {rules.length === 0 && !loadErr && <p>No Rules yet.</p>}
      <ul aria-label="Rules">
        {rules.map((r) => {
          const matchStr = Object.entries(r.match)
            .map(([k, v]) => `${k}: ${v}`)
            .join(", ");
          const isSessionOpen = !!openSessions[r.rule_id];
          const err = actionMsgs[r.rule_id];

          return (
            <li key={r.rule_id} className="rule-row" data-status={r.status}>
              <span className="rule-info">
                <strong>{r.rule_id}</strong> [{r.status}] target: {r.target} match: ({matchStr})
              </span>{" "}
              <button
                className="session-link"
                onClick={() => toggleSession(r.rule_id)}
              >
                {isSessionOpen ? `Hide session ${r.session_id}` : `Session ${r.session_id}`}
              </button>
              {r.status === "proposed" && (
                <>
                  <button onClick={() => handleApprove(r.rule_id)}>Approve</button>
                  <button onClick={() => handleReject(r.rule_id)}>Reject</button>
                </>
              )}
              {err && (
                <span role="alert" className="rule-error">
                  {err}
                </span>
              )}
              {isSessionOpen && (
                <div className="rule-session-container">
                  <SessionView sessionId={r.session_id} />
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
