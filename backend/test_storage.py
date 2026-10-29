"""Shared storage tests run against MemoryStore always, and against MongoStore
when MONGO_URI is set in the environment. Tests use a throwaway database name
and clean up after themselves.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from backend.gkmkb.storage import (
    CloseResult,
    MemoryStore,
    MongoStore,
    ReplayRecord,
    ReplayState,
    StorageBase,
)
from contracts.models import Alert, Detection, Entity, HoneypotSession, MitreTag, SessionEvent

T0 = datetime(2026, 10, 20, 10, 0, 0, tzinfo=UTC)
MONGO_URI = os.environ.get("MONGO_URI", "")


def _entity(src: str = "10.0.0.5", dst: str = "10.0.0.53") -> Entity:
    return Entity(src_ip=src, dst_ip=dst)


def _detection(
    detection_id: str = "run1-covertrace-0001",
    ts: datetime = T0,
    source: str = "covertrace",
) -> Detection:
    return Detection(
        detection_id=detection_id,
        source=source,  # type: ignore[arg-type]
        flow_id="f-001",
        entity=_entity(),
        ts=ts,
        score=0.91,
        label="dns-tunnel",
        features={"entropy": 4.1},
        threshold_used=3.5,
    )


def _alert(
    alert_id: str = "run1-alert-0001",
    ts: datetime = T0,
    status: str = "open",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        entity=_entity(),
        detection_ids=["run1-covertrace-0001", "run1-flowsight-0001"],
        severity="high",
        ts=ts,
        status=status,  # type: ignore[arg-type]
    )


def _replay(
    replay_id: str = "run1",
    started: datetime = T0,
    state: ReplayState = ReplayState.running,
) -> ReplayRecord:
    return ReplayRecord(
        replay_id=replay_id,
        pcap_name="test.pcap",
        started=started.isoformat(),
        state=state,
    )


@pytest.fixture
def memory_store() -> MemoryStore:
    return MemoryStore()


@pytest.fixture
def mongo_store():
    if not MONGO_URI:
        pytest.skip("MONGO_URI not set; skipping MongoDB tests")
    db_name = f"gkmkb_test_{uuid.uuid4().hex}"
    store = MongoStore(uri=MONGO_URI, db_name=db_name)
    yield store
    store._client.drop_database(db_name)
    store.close()


STORE_FIXTURES = ["memory_store", "mongo_store"]


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_and_get_replay(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    rec = _replay()
    store.save_replay(rec)
    got = store.get_replay("run1")
    assert got is not None
    assert got.replay_id == "run1"
    assert got.pcap_name == "test.pcap"
    assert got.state == ReplayState.running


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_update_replay(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    rec = _replay()
    store.save_replay(rec)
    store.update_replay("run1", state=ReplayState.done, flow_count=42)
    got = store.get_replay("run1")
    assert got is not None
    assert got.state == ReplayState.done
    assert got.flow_count == 42


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_replays_newest_first(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_replay(_replay("r1", T0))
    store.save_replay(_replay("r2", T0 + timedelta(seconds=10)))
    store.save_replay(_replay("r3", T0 + timedelta(seconds=20)))
    rows = store.list_replays()
    assert [r.replay_id for r in rows] == ["r3", "r2", "r1"]


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_replays_limit(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    for i in range(5):
        store.save_replay(_replay(f"r{i}", T0 + timedelta(seconds=i)))
    rows = store.list_replays(limit=3)
    assert len(rows) == 3


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_get_replay_missing_returns_none(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    assert store.get_replay("nonexistent") is None


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_and_list_detections(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    d = _detection()
    store.save_detection(d, "run1")
    rows = store.list_detections()
    assert len(rows) == 1
    assert rows[0].detection_id == d.detection_id


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_detections_newest_first(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_detection(_detection("run1-ct-0001", T0), "run1")
    store.save_detection(_detection("run1-ct-0002", T0 + timedelta(seconds=5)), "run1")
    store.save_detection(_detection("run1-ct-0003", T0 + timedelta(seconds=10)), "run1")
    rows = store.list_detections()
    assert [d.detection_id for d in rows] == ["run1-ct-0003", "run1-ct-0002", "run1-ct-0001"]


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_detections_filter_by_replay_id(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_detection(_detection("run1-ct-0001", T0), "run1")
    store.save_detection(_detection("run2-ct-0001", T0 + timedelta(seconds=1)), "run2")
    rows = store.list_detections(replay_id="run1")
    assert len(rows) == 1
    assert rows[0].detection_id == "run1-ct-0001"


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_detections_limit(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    for i in range(5):
        store.save_detection(_detection(f"run1-ct-{i:04d}", T0 + timedelta(seconds=i)), "run1")
    rows = store.list_detections(limit=3)
    assert len(rows) == 3


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_single_signal_detection_is_stored(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    single = _detection("run1-flowsight-0001", source="flowsight")
    store.save_detection(single, "run1")
    rows = store.list_detections()
    assert any(d.detection_id == "run1-flowsight-0001" for d in rows)


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_and_list_alerts(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    a = _alert()
    store.save_alert(a, "run1")
    rows = store.list_alerts()
    assert len(rows) == 1
    assert rows[0].alert_id == a.alert_id


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_alerts_newest_first(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001", T0), "run1")
    store.save_alert(_alert("run1-alert-0002", T0 + timedelta(seconds=5)), "run1")
    rows = store.list_alerts()
    assert [a.alert_id for a in rows] == ["run1-alert-0002", "run1-alert-0001"]


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_alerts_filter_by_replay_id(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001", T0), "run1")
    store.save_alert(_alert("run2-alert-0001", T0 + timedelta(seconds=1)), "run2")
    rows = store.list_alerts(replay_id="run2")
    assert len(rows) == 1
    assert rows[0].alert_id == "run2-alert-0001"


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_list_alerts_limit(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    for i in range(5):
        store.save_alert(_alert(f"run1-alert-{i:04d}", T0 + timedelta(seconds=i)), "run1")
    rows = store.list_alerts(limit=2)
    assert len(rows) == 2


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_close_alert_ok(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001"), "run1")
    result = store.close_alert("run1-alert-0001")
    assert result == CloseResult.ok
    rows = store.list_alerts()
    assert rows[0].status == "closed"


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_set_alert_engaged_attaches_session_to_open_alert(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001"), "run1")
    store.set_alert_engaged("run1-alert-0001", "s-1")
    alert = store.list_alerts()[0]
    assert (alert.status, alert.session_id) == ("engaged", "s-1")


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_set_alert_engaged_keeps_a_closed_alert_closed(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001"), "run1")
    store.close_alert("run1-alert-0001")
    store.set_alert_engaged("run1-alert-0001", "s-1")
    alert = store.list_alerts()[0]
    assert (alert.status, alert.session_id) == ("closed", "s-1")


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_close_alert_not_found(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    result = store.close_alert("does-not-exist")
    assert result == CloseResult.not_found


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_close_alert_already_closed(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001", status="closed"), "run1")
    result = store.close_alert("run1-alert-0001")
    assert result == CloseResult.already_closed


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_close_alert_twice_gives_already_closed(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_alert(_alert("run1-alert-0001"), "run1")
    assert store.close_alert("run1-alert-0001") == CloseResult.ok
    assert store.close_alert("run1-alert-0001") == CloseResult.already_closed


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_two_replays_do_not_mix_detections(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    store.save_detection(_detection("run1-ct-0001", T0), "run1")
    store.save_detection(_detection("run2-ct-0001", T0 + timedelta(seconds=1)), "run2")
    assert len(store.list_detections(replay_id="run1")) == 1
    assert len(store.list_detections(replay_id="run2")) == 1
    assert len(store.list_detections()) == 2


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_replay_upsert(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    rec = _replay()
    store.save_replay(rec)
    updated = rec.model_copy(update={"flow_count": 99})
    store.save_replay(updated)
    rows = store.list_replays()
    assert len(rows) == 1
    assert rows[0].flow_count == 99


def _session(
    session_id: str = "s-001",
    alert_id: str = "run1-alert-0001",
) -> HoneypotSession:
    return HoneypotSession(
        session_id=session_id,
        alert_id=alert_id,
        service="ssh",
        container_id="abc123",
        started=T0,
        events=[
            SessionEvent(ts=T0 + timedelta(seconds=2), type="command", data={"cmd": "whoami"}),
            SessionEvent(ts=T0, type="connect", data={"src": "10.0.0.5"}),
        ],
        mitre=[
            MitreTag(technique_id="T1033", name="System Owner/User Discovery", evidence="whoami"),
        ],
    )


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_and_get_session(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    s = _session()
    store.save_session(s)
    got = store.get_session("s-001")
    assert got is not None
    assert got.session_id == "s-001"
    assert got.alert_id == "run1-alert-0001"
    assert len(got.events) == 2


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_get_session_missing_returns_none(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    assert store.get_session("nonexistent") is None


@pytest.mark.parametrize("store_fixture", STORE_FIXTURES)
def test_save_session_upsert(store_fixture, request):
    store: StorageBase = request.getfixturevalue(store_fixture)
    s = _session()
    store.save_session(s)
    updated = s.model_copy(update={"service": "telnet"})
    store.save_session(updated)
    got = store.get_session("s-001")
    assert got is not None
    assert got.service == "telnet"
