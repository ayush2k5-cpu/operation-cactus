from datetime import UTC, datetime, timedelta

from backend.gkmkb.gate import Gate
from contracts.models import Detection

T0 = datetime(2026, 10, 20, 10, 0, tzinfo=UTC)


def det(source, seconds=0.0, score=0.9, src="10.0.0.5", n=1):
    return Detection(
        detection_id=f"{source}-{n}",
        source=source,
        flow_id="f-1",
        entity={"src_ip": src, "dst_ip": "10.0.0.53"},
        ts=T0 + timedelta(seconds=seconds),
        score=score,
        label="x",
        threshold_used=0.5,
    )


def test_both_signals_raise_one_alert():
    gate = Gate()
    assert gate.feed(det("flowsight", 0)) is None
    alert = gate.feed(det("covertrace", 5))
    assert alert is not None
    assert alert.entity.src_ip == "10.0.0.5"
    assert sorted(alert.detection_ids) == ["covertrace-1", "flowsight-1"]
    assert alert.status == "open"


def test_single_signal_raises_nothing():
    gate = Gate()
    for i in range(5):
        assert gate.feed(det("covertrace", i, n=i)) is None


def test_detection_outside_window_does_not_count():
    gate = Gate(window_seconds=60)
    gate.feed(det("flowsight", 0))
    assert gate.feed(det("covertrace", 120)) is None


def test_below_threshold_is_ignored():
    gate = Gate(threshold=0.7)
    gate.feed(det("flowsight", 0, score=0.5))
    assert gate.feed(det("covertrace", 1, score=0.9)) is None


def test_one_open_alert_per_entity_until_closed():
    gate = Gate()
    gate.feed(det("flowsight", 0))
    first = gate.feed(det("covertrace", 1))
    assert first is not None
    assert gate.feed(det("flowsight", 2, n=2)) is None
    gate.close(first)
    assert gate.feed(det("covertrace", 3, n=3)) is not None


def test_different_entities_do_not_mix():
    gate = Gate()
    gate.feed(det("flowsight", 0, src="10.0.0.5"))
    assert gate.feed(det("covertrace", 1, src="10.0.0.6")) is None
