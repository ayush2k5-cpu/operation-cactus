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
from backend.gkmkb.storage import ReplayRecord, ReplayState, StorageBase
from capture.replay import ReplaySource
from contracts.models import Alert


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
