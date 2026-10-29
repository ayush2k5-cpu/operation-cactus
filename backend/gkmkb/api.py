"""Replay API: start a replay in a background worker, push live events over a WebSocket."""

import asyncio
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.gkmkb.gate import Gate
from backend.gkmkb.pipeline import default_detectors, stream
from backend.gkmkb.settings import load_settings
from backend.gkmkb.storage import CloseResult, ReplayRecord, ReplayState, StorageBase
from capture.replay import ReplaySource
from contracts.models import Alert

_LIST_DEFAULT = 50
_LIST_MAX = 500


class ReplayRequest(BaseModel):
    pcap: str


class EventHub:
    """Fan out messages from the worker thread to every connected WebSocket client."""

    def __init__(self) -> None:
        self._clients: set[tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = set()
        self._lock = threading.Lock()

    def add(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue) -> None:
        with self._lock:
            self._clients.add((loop, queue))

    def remove(self, loop: asyncio.AbstractEventLoop, queue: asyncio.Queue) -> None:
        with self._lock:
            self._clients.discard((loop, queue))

    def publish(self, message: dict) -> None:
        with self._lock:
            clients = list(self._clients)
        for loop, queue in clients:
            try:
                loop.call_soon_threadsafe(queue.put_nowait, message)
            except RuntimeError:
                self.remove(loop, queue)


def create_app(
    store: StorageBase,
    data_dir: str | Path | None = None,
    event_delay_ms: float | None = None,
) -> FastAPI:
    settings = load_settings()
    root = Path(settings.data_dir if data_dir is None else data_dir).resolve()
    delay = (settings.replay_event_delay_ms if event_delay_ms is None else event_delay_ms) / 1000
    hub = EventHub()
    busy = threading.Lock()
    app = FastAPI(title="GKMKB")

    _active_gate: list[Gate] = []
    _active_gate_lock = threading.Lock()

    def run_replay(replay_id: str, pcap: Path) -> None:
        flows = detections = alerts = 0
        state, error = ReplayState.done, None
        try:
            if not pcap.is_file():
                raise FileNotFoundError(pcap.name)
            window = settings.gate_window_seconds

            def counted():
                nonlocal flows
                for flow in ReplaySource(pcap).flows():
                    flows += 1
                    yield flow

            gate = Gate(window_seconds=window, threshold=settings.gate_threshold)
            with _active_gate_lock:
                _active_gate.clear()
                _active_gate.append(gate)
            for event in stream(counted(), default_detectors(window), gate, replay_id):
                if isinstance(event, Alert):
                    store.save_alert(event, replay_id)
                    alerts += 1
                    kind = "alert"
                else:
                    store.save_detection(event, replay_id)
                    detections += 1
                    kind = "detection"
                hub.publish(
                    {"type": kind, "replay_id": replay_id, "data": event.model_dump(mode="json")}
                )
                if delay > 0:
                    time.sleep(delay)
        except Exception as exc:
            state, error = ReplayState.failed, f"{type(exc).__name__}: {exc}"
        finally:
            with _active_gate_lock:
                _active_gate.clear()
            counts = {
                "flow_count": flows,
                "detection_count": detections,
                "alert_count": alerts,
            }
            store.update_replay(
                replay_id,
                ended=datetime.now(UTC).isoformat(),
                state=state,
                error=error,
                **counts,
            )
            hub.publish(
                {
                    "type": "replay_done",
                    "replay_id": replay_id,
                    "data": {"state": state.value, "error": error, **counts},
                }
            )
            busy.release()

    @app.get("/api/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.post("/api/replay")
    def start_replay(req: ReplayRequest) -> dict:
        pcap = (root / req.pcap).resolve()
        if not pcap.is_relative_to(root):
            raise HTTPException(400, "pcap must be inside the data folder")
        if not busy.acquire(blocking=False):
            raise HTTPException(409, "a replay is already running")
        replay_id = uuid4().hex[:8]
        store.save_replay(
            ReplayRecord(
                replay_id=replay_id,
                pcap_name=req.pcap,
                started=datetime.now(UTC).isoformat(),
            )
        )
        threading.Thread(target=run_replay, args=(replay_id, pcap), daemon=True).start()
        return {"replay_id": replay_id}

    @app.get("/api/replays")
    def list_replays(limit: int = _LIST_DEFAULT) -> list[dict]:
        limit = min(limit, _LIST_MAX)
        return [r.model_dump(mode="json") for r in store.list_replays(limit=limit)]

    @app.get("/api/detections")
    def list_detections(replay_id: str | None = None, limit: int = _LIST_DEFAULT) -> list[dict]:
        limit = min(limit, _LIST_MAX)
        return [
            d.model_dump(mode="json")
            for d in store.list_detections(replay_id=replay_id, limit=limit)
        ]

    @app.get("/api/alerts")
    def list_alerts(replay_id: str | None = None, limit: int = _LIST_DEFAULT) -> list[dict]:
        limit = min(limit, _LIST_MAX)
        return [
            a.model_dump(mode="json") for a in store.list_alerts(replay_id=replay_id, limit=limit)
        ]

    @app.post("/api/alerts/{alert_id}/close")
    def close_alert(alert_id: str) -> dict:
        all_alerts = store.list_alerts(limit=_LIST_MAX)
        target = next((a for a in all_alerts if a.alert_id == alert_id), None)
        result = store.close_alert(alert_id)
        if result == CloseResult.not_found:
            raise HTTPException(404, "alert not found")
        if result == CloseResult.already_closed:
            raise HTTPException(409, "alert already closed")
        if target is not None:
            with _active_gate_lock:
                if _active_gate:
                    _active_gate[0].close(target)
        return {"status": "closed"}

    @app.get("/api/pcaps")
    def list_pcaps() -> list[str]:
        if not root.is_dir():
            return []
        names = sorted(p.name for p in root.iterdir() if p.is_file())
        return names

    @app.get("/api/sessions/{session_id}")
    def get_session(session_id: str) -> dict:
        session = store.get_session(session_id)
        if session is None:
            raise HTTPException(404, "session not found")
        data = session.model_dump(mode="json")
        data["events"] = sorted(data["events"], key=lambda e: e["ts"])
        return data

    def publish_session_event(session_id: str, event: dict) -> None:
        """Push one session event to all connected WebSocket clients."""
        hub.publish({"type": "session_event", "session_id": session_id, "data": event})

    app.state.publish_session_event = publish_session_event

    @app.websocket("/ws/events")
    async def events(ws: WebSocket) -> None:
        await ws.accept()
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()
        hub.add(loop, queue)
        try:
            while True:
                await ws.send_json(await queue.get())
        except WebSocketDisconnect:
            pass
        finally:
            hub.remove(loop, queue)

    return app
