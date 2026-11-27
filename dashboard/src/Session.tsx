import { useEffect, useState } from "react";
import { type Session, type SessionEvent, getSession } from "./api/client";

export function SessionView({
  sessionId,
  liveEvents = [],
}: {
  sessionId: string;
  liveEvents?: SessionEvent[];
}) {
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

  const seen = new Set<string>();
  const allEvents: SessionEvent[] = [];
  for (const e of [...session.events, ...liveEvents]) {
    const key = `${e.ts}|${e.type}|${JSON.stringify(e.data)}`;
    if (!seen.has(key)) {
      seen.add(key);
      allEvents.push(e);
    }
  }
  allEvents.sort((a, b) => a.ts.localeCompare(b.ts));

  const connectEvent = allEvents.find((e) => e.type === "connect");
  const attacker = connectEvent?.data.attacker_addr ?? connectEvent?.data.src;

  return (
    <div aria-label="Honeypot session">
      <h4>Honeypot session {session.session_id}</h4>
      {attacker && <p>Attacker address: {attacker}</p>}
      {allEvents.length === 0 ? (
        <p>No events recorded in this session.</p>
      ) : (
        <ol aria-label="Session events">
          {allEvents.map((e, i) => (
            <li key={i}>
              {e.ts} {e.type} {e.data.line ?? e.data.cmd ?? e.data.reason ?? ""}
            </li>
          ))}
        </ol>
      )}
      {session.mitre.length === 0 ? (
        <p>MITRE tags: no tag</p>
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
