"""Storage interface for Detections, Alerts and replay records (ADR 0005).

Two implementations ship here:
- ``MemoryStore``: in-memory, no dependencies; always used in tests.
- ``MongoStore``: MongoDB via pymongo; used only when a database address is available.

Neither implementation is called by detectors or the Gate. The backend wires
the pipeline output to whichever store is active.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from pydantic import BaseModel

from contracts.models import Alert, Detection


class ReplayState(str, Enum):
    running = "running"
    done = "done"
    failed = "failed"


class ReplayRecord(BaseModel):
    """Persistent record for one replay run."""

    replay_id: str
    pcap_name: str
    started: str
    ended: str | None = None
    state: ReplayState = ReplayState.running
    error: str | None = None
    flow_count: int = 0
    detection_count: int = 0
    alert_count: int = 0


class CloseResult(str, Enum):
    ok = "ok"
    not_found = "not_found"
    already_closed = "already_closed"


class StorageBase(ABC):
    """Minimal interface the backend uses to persist pipeline output."""

    @abstractmethod
    def save_replay(self, record: ReplayRecord) -> None:
        """Insert or replace a replay record."""

    @abstractmethod
    def update_replay(self, replay_id: str, **fields: object) -> None:
        """Patch scalar fields on an existing replay record."""

    @abstractmethod
    def get_replay(self, replay_id: str) -> ReplayRecord | None:
        """Return one replay record, or None if not found."""

    @abstractmethod
    def list_replays(self, *, limit: int = 50) -> list[ReplayRecord]:
        """Return replay records, newest first, up to *limit*."""

    @abstractmethod
    def save_detection(self, detection: Detection, replay_id: str) -> None:
        """Persist one Detection (including single-signal ones)."""

    @abstractmethod
    def list_detections(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Detection]:
        """Return Detections, newest first, optionally filtered by *replay_id*."""

    @abstractmethod
    def save_alert(self, alert: Alert, replay_id: str) -> None:
        """Persist one Alert."""

    @abstractmethod
    def list_alerts(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        """Return Alerts, newest first, optionally filtered by *replay_id*."""

    @abstractmethod
    def close_alert(self, alert_id: str) -> CloseResult:
        """Mark an Alert closed.

        Returns:
            CloseResult.ok            – closed successfully.
            CloseResult.not_found     – no Alert with that id.
            CloseResult.already_closed – Alert exists but was already closed.
        """


class MemoryStore(StorageBase):
    """In-memory store. No I/O, no dependencies. Safe to use in every test."""

    def __init__(self) -> None:
        self._replays: dict[str, ReplayRecord] = {}
        self._replay_order: list[str] = []
        self._detections: list[tuple[Detection, str]] = []
        self._alerts: list[tuple[Alert, str]] = []

    def save_replay(self, record: ReplayRecord) -> None:
        if record.replay_id not in self._replays:
            self._replay_order.append(record.replay_id)
        self._replays[record.replay_id] = record

    def update_replay(self, replay_id: str, **fields: object) -> None:
        record = self._replays.get(replay_id)
        if record is None:
            return
        self._replays[replay_id] = record.model_copy(update=fields)

    def get_replay(self, replay_id: str) -> ReplayRecord | None:
        return self._replays.get(replay_id)

    def list_replays(self, *, limit: int = 50) -> list[ReplayRecord]:
        ordered = [self._replays[rid] for rid in reversed(self._replay_order)]
        return ordered[:limit]

    def save_detection(self, detection: Detection, replay_id: str) -> None:
        self._detections.append((detection, replay_id))

    def list_detections(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Detection]:
        rows = list(reversed(self._detections))
        if replay_id is not None:
            rows = [(d, rid) for d, rid in rows if rid == replay_id]
        return [d for d, _ in rows[:limit]]

    def save_alert(self, alert: Alert, replay_id: str) -> None:
        self._alerts.append((alert, replay_id))

    def list_alerts(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        rows = list(reversed(self._alerts))
        if replay_id is not None:
            rows = [(a, rid) for a, rid in rows if rid == replay_id]
        return [a for a, _ in rows[:limit]]

    def close_alert(self, alert_id: str) -> CloseResult:
        for i, (alert, replay_id) in enumerate(self._alerts):
            if alert.alert_id == alert_id:
                if alert.status == "closed":
                    return CloseResult.already_closed
                self._alerts[i] = (alert.model_copy(update={"status": "closed"}), replay_id)
                return CloseResult.ok
        return CloseResult.not_found


class MongoStore(StorageBase):
    """MongoDB-backed store (ADR 0005). Requires a running mongod.

    Callers pass ``replay_id`` explicitly to ``save_detection`` and
    ``save_alert`` so the value is indexed and filtered without parsing IDs.
    """

    def __init__(self, uri: str, db_name: str) -> None:
        import pymongo

        self._client: pymongo.MongoClient = pymongo.MongoClient(uri)
        db = self._client[db_name]
        self._replays_col = db["replays"]
        self._detections_col = db["detections"]
        self._alerts_col = db["alerts"]
        self._replays_col.create_index([("started", pymongo.DESCENDING)])
        self._detections_col.create_index([("ts", pymongo.DESCENDING)])
        self._detections_col.create_index("replay_id")
        self._alerts_col.create_index([("ts", pymongo.DESCENDING)])
        self._alerts_col.create_index("replay_id")

    def close(self) -> None:
        self._client.close()

    def save_replay(self, record: ReplayRecord) -> None:
        doc = record.model_dump(mode="json")
        self._replays_col.replace_one({"replay_id": record.replay_id}, doc, upsert=True)

    def update_replay(self, replay_id: str, **fields: object) -> None:
        self._replays_col.update_one({"replay_id": replay_id}, {"$set": fields})

    def get_replay(self, replay_id: str) -> ReplayRecord | None:
        doc = self._replays_col.find_one({"replay_id": replay_id}, {"_id": 0})
        if doc is None:
            return None
        return ReplayRecord.model_validate(doc)

    def list_replays(self, *, limit: int = 50) -> list[ReplayRecord]:
        cursor = self._replays_col.find({}, {"_id": 0}).sort("started", -1).limit(limit)
        return [ReplayRecord.model_validate(doc) for doc in cursor]

    def save_detection(self, detection: Detection, replay_id: str) -> None:
        doc = detection.model_dump(mode="json")
        doc["replay_id"] = replay_id
        self._detections_col.insert_one(doc)

    def list_detections(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Detection]:
        filt: dict[str, object] = {}
        if replay_id is not None:
            filt["replay_id"] = replay_id
        cursor = (
            self._detections_col.find(filt, {"_id": 0, "replay_id": 0}).sort("ts", -1).limit(limit)
        )
        return [Detection.model_validate(doc) for doc in cursor]

    def save_alert(self, alert: Alert, replay_id: str) -> None:
        doc = alert.model_dump(mode="json")
        doc["replay_id"] = replay_id
        self._alerts_col.insert_one(doc)

    def list_alerts(
        self,
        *,
        replay_id: str | None = None,
        limit: int = 100,
    ) -> list[Alert]:
        filt: dict[str, object] = {}
        if replay_id is not None:
            filt["replay_id"] = replay_id
        cursor = self._alerts_col.find(filt, {"_id": 0, "replay_id": 0}).sort("ts", -1).limit(limit)
        return [Alert.model_validate(doc) for doc in cursor]

    def close_alert(self, alert_id: str) -> CloseResult:
        doc = self._alerts_col.find_one({"alert_id": alert_id}, {"_id": 0})
        if doc is None:
            return CloseResult.not_found
        if doc["status"] == "closed":
            return CloseResult.already_closed
        self._alerts_col.update_one({"alert_id": alert_id}, {"$set": {"status": "closed"}})
        return CloseResult.ok
