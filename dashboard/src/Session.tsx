import { useEffect, useState } from "react";
import { type Session, getSession } from "./api/client";

export function SessionView({ sessionId }: { sessionId: string }) {
  const [session, setSession] = useState<Session | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getSession(sessionId)
      .then((s) => {
        setSession(s);
        setError(null);
      })
      .catch(() => setError("Could not load the session."));
  }, [sessionId]);

  if (error) return <p role="alert">{error}</p>;
  if (!session) return <p>Loading the session...</p>;

  const events = [...session.events].sort((a, b) => a.ts.localeCompare(b.ts));
  const attacker = events.find((e) => e.type === "connect")?.data.attacker_addr;
  return (
    <div aria-label="Honeypot session">
      <h4>Honeypot session {session.session_id}</h4>
      {attacker && <p>Attacker address: {attacker}</p>}
      <ol aria-label="Session events">
        {events.map((e, i) => (
          <li key={i}>
            {e.ts} {e.type} {e.data.line ?? e.data.reason ?? ""}
          </li>
        ))}
      </ol>
      {session.mitre.length === 0 ? (
        <p>MITRE tags: none yet</p>
      ) : (
        <ul aria-label="MITRE tags">
          {session.mitre.map((t) => (
            <li key={t.technique_id}>
              {t.technique_id} {t.name}: {t.evidence}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
