import { useState } from "react";
import { Bar, BarChart, Legend, Tooltip, XAxis, YAxis } from "recharts";
import { type Detection, type ReplayRecord, listDetections } from "./api/client";

const BACKEND_DOWN = "Backend is down. Start the backend and try again.";
const NO_DETECTION = "no Detection, so no threshold shown";

type Side = { record: ReplayRecord; detections: Detection[] };

function coverTrace(side: Side): Detection[] {
  return side.detections.filter((d) => d.source === "covertrace");
}

function ReplayPicker(props: {
  label: string;
  replays: ReplayRecord[];
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <label>
      {props.label}
      <select value={props.value} onChange={(e) => props.onChange(e.target.value)}>
        <option value="">Pick a replay</option>
        {props.replays.map((r) => (
          <option key={r.replay_id} value={r.replay_id}>
            {r.replay_id} ({r.pcap_name})
          </option>
        ))}
      </select>
    </label>
  );
}

function SideTable({ side }: { side: Side }) {
  const dets = coverTrace(side);
  return (
    <section aria-label={`Replay ${side.record.replay_id}`}>
      <h3>
        Replay {side.record.replay_id} ({side.record.pcap_name})
      </h3>
      {dets.length === 0 ? (
        <p>{NO_DETECTION}</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Label</th>
              <th>threshold_used</th>
              <th>score</th>
            </tr>
          </thead>
          <tbody>
            {dets.map((d) => (
              <tr key={d.detection_id}>
                <td>{d.label}</td>
                <td>{d.threshold_used}</td>
                <td>{d.score.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export function Compare({ replays, onBack }: { replays: ReplayRecord[]; onBack: () => void }) {
  const [ids, setIds] = useState(["", ""]);
  const [sides, setSides] = useState<(Side | null)[]>([null, null]);
  const [err, setErr] = useState<string | null>(null);

  const pick = (i: number, id: string) => {
    setIds((prev) => prev.map((p, j) => (j === i ? id : p)));
    const record = replays.find((r) => r.replay_id === id);
    const set = (side: Side | null) =>
      setSides((prev) => prev.map((s, j) => (j === i ? side : s)));
    if (!record) return set(null);
    listDetections(id)
      .then((detections) => {
        set({ record, detections });
        setErr(null);
      })
      .catch(() => setErr(BACKEND_DOWN));
  };

  const chosen = sides.filter((s): s is Side => s !== null);
  const chartData = chosen.flatMap((s) => {
    const top = coverTrace(s).sort((a, b) => b.score - a.score)[0];
    return top
      ? [{ name: s.record.replay_id, threshold_used: top.threshold_used, score: top.score }]
      : [];
  });

  return (
    <section>
      <button onClick={onBack}>Back to Replays</button>
      <h2>Threshold compare (from Detections)</h2>
      <p>CoverTrace Detections only: threshold_used and score for each replay.</p>
      {err && <p role="alert">{err}</p>}
      <ReplayPicker label="First replay" replays={replays} value={ids[0]} onChange={(v) => pick(0, v)} />
      <ReplayPicker label="Second replay" replays={replays} value={ids[1]} onChange={(v) => pick(1, v)} />
      {chartData.length > 0 && (
        <BarChart width={420} height={240} data={chartData} aria-label="Threshold compare chart">
          <XAxis dataKey="name" />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Legend />
          <Bar dataKey="threshold_used" isAnimationActive={false} />
          <Bar dataKey="score" isAnimationActive={false} />
        </BarChart>
      )}
      {chosen.map((s) => (
        <SideTable key={s.record.replay_id} side={s} />
      ))}
    </section>
  );
}
