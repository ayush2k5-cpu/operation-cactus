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


def test_health_returns_ok(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_replays_newest_first(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_messages(client, "control.pcap")
    replay_messages(client, "mix.pcap")
    resp = client.get("/api/replays")
    assert resp.status_code == 200
    records = resp.json()
    assert len(records) == 2
    assert records[0]["pcap_name"] == "mix.pcap"
    assert records[1]["pcap_name"] == "control.pcap"


def test_list_replays_limit(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_messages(client, "control.pcap")
    replay_messages(client, "mix.pcap")
    resp = client.get("/api/replays", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_detections_filter_by_replay(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    first, _ = replay_messages(client, "mix.pcap")
    second, _ = replay_messages(client, "control.pcap")
    resp = client.get("/api/detections", params={"replay_id": first})
    assert resp.status_code == 200
    ids = {d["detection_id"] for d in resp.json()}
    assert all(i.startswith(first) for i in ids)
    assert not any(i.startswith(second) for i in ids)


def test_list_detections_includes_single_signal(data_dir, store):
    build(data_dir / "single.pcap", [("10.0.0.8", benign_labels(30), [0.1])])
    client = TestClient(create_app(store, data_dir))
    replay_id, _ = replay_messages(client, "single.pcap")
    resp = client.get("/api/detections", params={"replay_id": replay_id})
    assert resp.status_code == 200
    assert len(resp.json()) > 0
    assert client.get("/api/alerts", params={"replay_id": replay_id}).json() == []


def test_list_detections_limit(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_messages(client, "mix.pcap")
    resp = client.get("/api/detections", params={"limit": 1})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_list_alerts_filter_by_replay(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    first, _ = replay_messages(client, "mix.pcap")
    second, _ = replay_messages(client, "mix.pcap")
    resp_first = client.get("/api/alerts", params={"replay_id": first})
    resp_second = client.get("/api/alerts", params={"replay_id": second})
    assert resp_first.status_code == 200
    assert resp_second.status_code == 200
    assert len(resp_first.json()) == 1
    assert len(resp_second.json()) == 1
    assert resp_first.json()[0]["alert_id"] != resp_second.json()[0]["alert_id"]


def test_close_alert_ok(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_id, _ = replay_messages(client, "mix.pcap")
    alerts = client.get("/api/alerts", params={"replay_id": replay_id}).json()
    alert_id = alerts[0]["alert_id"]
    resp = client.post(f"/api/alerts/{alert_id}/close")
    assert resp.status_code == 200
    assert resp.json() == {"status": "closed"}
    updated = client.get("/api/alerts", params={"replay_id": replay_id}).json()
    assert updated[0]["status"] == "closed"


def test_close_alert_unknown_gives_404(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    resp = client.post("/api/alerts/no-such-alert/close")
    assert resp.status_code == 404


def test_close_alert_already_closed_gives_409(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    replay_id, _ = replay_messages(client, "mix.pcap")
    alerts = client.get("/api/alerts", params={"replay_id": replay_id}).json()
    alert_id = alerts[0]["alert_id"]
    client.post(f"/api/alerts/{alert_id}/close")
    resp = client.post(f"/api/alerts/{alert_id}/close")
    assert resp.status_code == 409


def test_close_alert_allows_same_entity_to_alert_again(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    first_id, _ = replay_messages(client, "mix.pcap")
    alerts_before = client.get("/api/alerts", params={"replay_id": first_id}).json()
    alert_id = alerts_before[0]["alert_id"]
    client.post(f"/api/alerts/{alert_id}/close")
    second_id, _ = replay_messages(client, "mix.pcap")
    alerts_after = client.get("/api/alerts", params={"replay_id": second_id}).json()
    assert len(alerts_after) == 1


def test_list_pcaps_returns_sorted_names(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    resp = client.get("/api/pcaps")
    assert resp.status_code == 200
    names = resp.json()
    assert names == sorted(names)
    assert "mix.pcap" in names
    assert "control.pcap" in names


def test_list_pcaps_empty_dir(tmp_path, store):
    empty = tmp_path / "empty"
    empty.mkdir()
    client = TestClient(create_app(store, empty))
    resp = client.get("/api/pcaps")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_pcaps_missing_dir(tmp_path, store):
    missing = tmp_path / "missing"
    client = TestClient(create_app(store, missing))
    resp = client.get("/api/pcaps")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_pcaps_no_path_traversal(data_dir, store):
    client = TestClient(create_app(store, data_dir))
    names = client.get("/api/pcaps").json()
    assert all("/" not in n and "\\" not in n for n in names)
