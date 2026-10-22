import pytest
from fastapi.testclient import TestClient

from backend.gkmkb.api import create_app
from backend.gkmkb.storage import MemoryStore, ReplayState
from backend.test_pipeline import benign_labels, build, tunnel_labels


@pytest.fixture
def data_dir(tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    build(
        root / "mix.pcap",
        [
            ("10.0.0.5", tunnel_labels(30), [0.1]),
            ("10.0.0.6", benign_labels(30), [2.0, 9.0, 4.5, 15.0, 1.0]),
        ],
    )
    build(root / "control.pcap", [("10.0.0.6", benign_labels(30), [2.0, 9.0, 4.5, 15.0, 1.0])])
    return root


@pytest.fixture
def store():
    return MemoryStore()


def replay_messages(client, pcap):
    """Connect first, start the replay, read live messages up to replay_done."""
    with client.websocket_connect("/ws/events") as ws:
        resp = client.post("/api/replay", json={"pcap": pcap})
        assert resp.status_code == 200
        replay_id = resp.json()["replay_id"]
        messages = []
        while True:
            message = ws.receive_json()
            messages.append(message)
            if message["type"] == "replay_done":
                return replay_id, messages


def test_tunnel_replay_streams_and_stores(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_id, messages = replay_messages(client, "mix.pcap")

    kinds = [m["type"] for m in messages]
    assert kinds.count("alert") == 1
    assert kinds.count("detection") > 0
    assert kinds[-1] == "replay_done"
    assert all(m["replay_id"] == replay_id for m in messages)

    done = messages[-1]["data"]
    assert done["state"] == "done"
    stored_detections = store.list_detections(replay_id=replay_id)
    stored_alerts = store.list_alerts(replay_id=replay_id)
    assert len(stored_detections) == kinds.count("detection") == done["detection_count"]
    assert len(stored_alerts) == 1 == done["alert_count"]
    assert messages[kinds.index("alert")]["data"]["alert_id"] == stored_alerts[0].alert_id
    assert store.get_replay(replay_id).state == ReplayState.done


def test_control_pcap_gives_no_alert(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_id, messages = replay_messages(client, "control.pcap")
    assert [m for m in messages if m["type"] == "alert"] == []
    assert store.list_alerts(replay_id=replay_id) == []


def test_two_replays_never_share_ids(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    first, _ = replay_messages(client, "mix.pcap")
    second, _ = replay_messages(client, "mix.pcap")
    assert first != second
    ids_a = {d.detection_id for d in store.list_detections(replay_id=first)}
    ids_b = {d.detection_id for d in store.list_detections(replay_id=second)}
    assert ids_a and ids_b and not ids_a & ids_b


def test_second_replay_while_running_gets_409(data_dir, store):
    client = TestClient(create_app(store, data_dir, event_delay_ms=20))
    with client.websocket_connect("/ws/events") as ws:
        assert client.post("/api/replay", json={"pcap": "mix.pcap"}).status_code == 200
        assert client.post("/api/replay", json={"pcap": "mix.pcap"}).status_code == 409
        while ws.receive_json()["type"] != "replay_done":
            pass


def test_path_outside_data_folder_is_rejected(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    resp = client.post("/api/replay", json={"pcap": "../outside.pcap"})
    assert resp.status_code == 400
    assert store.list_replays() == []


def test_missing_pcap_is_recorded_as_failed(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_id, messages = replay_messages(client, "nope.pcap")
    done = messages[-1]["data"]
    assert done["state"] == "failed"
    assert "nope.pcap" in done["error"]
    record = store.get_replay(replay_id)
    assert record.state == ReplayState.failed
    assert record.error == done["error"]


def test_disconnected_client_does_not_stop_replay(data_dir, store):
    client = TestClient(create_app(store, data_dir, event_delay_ms=5))
    with client.websocket_connect("/ws/events") as ws:
        replay_id = client.post("/api/replay", json={"pcap": "mix.pcap"}).json()["replay_id"]
        ws.receive_json()
    _, messages = replay_messages_after_reconnect(client)
    assert messages[-1]["type"] == "replay_done"
    assert store.get_replay(replay_id).state == ReplayState.done
    assert len(store.list_alerts(replay_id=replay_id)) == 1


def replay_messages_after_reconnect(client):
    """Reconnect mid-replay and read until the running replay finishes."""
    with client.websocket_connect("/ws/events") as ws:
        messages = []
        while True:
            message = ws.receive_json()
            messages.append(message)
            if message["type"] == "replay_done":
                return message["replay_id"], messages


def test_delay_setting_paces_the_replay(data_dir, store):
    import time

    client = TestClient(create_app(store, data_dir, event_delay_ms=30))
    start = time.monotonic()
    _, messages = replay_messages(client, "mix.pcap")
    events = len(messages) - 1
    assert time.monotonic() - start >= events * 0.03 * 0.9
