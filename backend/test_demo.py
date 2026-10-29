"""The review demo, end to end through the API on the real demo pcaps.

Same steps as the demo: replay the tunnel pcap, the control and the hard benign pcap,
then a file that is not a pcap. The honeypot is a fake here; the real container is
covered by the Docker-marked test in mimicnet.
"""

from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from backend.gkmkb.api import create_app
from backend.gkmkb.storage import MemoryStore
from contracts.models import HoneypotSession, SessionEvent

DEMO_DIR = Path(__file__).resolve().parent.parent / "data" / "demo"


def fake_engage(alert):
    now = datetime(2026, 10, 30, tzinfo=UTC)
    return HoneypotSession(
        session_id="demo-session",
        alert_id=alert.alert_id,
        service="ssh-like",
        container_id="fake",
        started=now,
        events=[SessionEvent(ts=now, type="connect", data={"attacker_addr": "192.0.2.50"})],
    )


def replay(client, pcap):
    with client.websocket_connect("/ws/events") as ws:
        replay_id = client.post("/api/replay", json={"pcap": pcap}).json()["replay_id"]
        while ws.receive_json()["type"] != "replay_done":
            pass
    return replay_id


def test_the_review_demo_steps():
    store = MemoryStore()
    client = TestClient(create_app(store, DEMO_DIR, engage_fn=fake_engage))

    tunnel = replay(client, "dns_tunnel_plus_benign.pcap")
    assert len(store.list_detections(replay_id=tunnel)) == 2
    assert {d.source for d in store.list_detections(replay_id=tunnel)} == {
        "flowsight",
        "covertrace",
    }
    assert len(store.list_alerts(replay_id=tunnel)) == 1

    control = replay(client, "single_signal_control.pcap")
    assert store.list_alerts(replay_id=control) == []

    hard = replay(client, "hard_benign_dns.pcap")
    assert store.list_alerts(replay_id=hard) == []


def test_the_demo_pcap_list_has_only_pcaps():
    names = TestClient(create_app(MemoryStore(), DEMO_DIR)).get("/api/pcaps").json()
    assert names == [
        "dns_tunnel_plus_benign.pcap",
        "hard_benign_dns.pcap",
        "single_signal_control.pcap",
    ]
