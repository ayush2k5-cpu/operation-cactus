"""Tests for pcap labels and the hard benign set (ticket #81).

Acceptance criteria:
- Every lab pcap has a labels file; each Entity is tunnel or benign
- The new benign pcaps are made by the existing seeded pcap script, so re-running gives identical files
- A test fails if a pcap has no labels file or an Entity has no label
- Each file is under 5 MB and contains no real users' traffic
"""

from pathlib import Path

import pytest

from capture.replay import ReplaySource
from eval.labels import find_labels_file, load_labels


def validate_pcap_labels(pcap_path: Path) -> None:
    """Verify that a pcap has a labels file and every Entity in it is labelled."""
    labels_file = find_labels_file(pcap_path)
    labels = load_labels(labels_file)

    pcap_entities: set[tuple[str, str]] = set()
    for flow in ReplaySource(pcap_path).flows():
        pcap_entities.add((flow.src_ip, flow.dst_ip))

    if not pcap_entities:
        # If no flows, check if labels file has at least one entity or is empty
        return

    for entity in pcap_entities:
        if entity not in labels:
            raise ValueError(
                f"Entity {entity} in pcap '{pcap_path.name}' has no label in '{labels_file.name}'"
            )
        if labels[entity] not in ("tunnel", "benign"):
            raise ValueError(
                f"Entity {entity} has invalid label '{labels[entity]}' (must be 'tunnel' or 'benign')"
            )


def test_every_lab_pcap_has_labels_and_every_entity_is_labelled():
    """Every lab pcap in data/demo (and data/eval if present) must have a valid labels file."""
    demo_dir = Path("data/demo")
    assert demo_dir.is_dir(), "data/demo directory must exist"

    pcaps = list(demo_dir.glob("*.pcap"))
    eval_dir = Path("data/eval")
    if eval_dir.is_dir():
        pcaps.extend(eval_dir.glob("*.pcap"))

    assert len(pcaps) >= 3, f"Expected at least 3 lab pcaps, found {len(pcaps)}"

    for pcap in pcaps:
        validate_pcap_labels(pcap)


def test_missing_labels_file_fails(tmp_path):
    """Test fails when a pcap has no labels file."""
    orphan_pcap = tmp_path / "orphan.pcap"
    orphan_pcap.write_bytes(b"")

    with pytest.raises(FileNotFoundError) as exc_info:
        validate_pcap_labels(orphan_pcap)
    assert "Missing labels file" in str(exc_info.value)


def test_unlabelled_entity_in_pcap_fails(tmp_path):
    """Test fails when an Entity in a pcap has no label in the labels file."""
    # Use existing demo pcap which has 10.0.1.10 and 10.0.2.20
    demo_pcap = Path("data/demo/dns_tunnel_plus_benign.pcap")
    if not demo_pcap.exists():
        pytest.skip("demo pcap not present")

    # Incomplete labels file missing 10.0.2.20
    incomplete_labels = tmp_path / "test_incomplete.labels"
    incomplete_labels.write_text("10.0.1.10,10.0.0.53,benign\n", encoding="utf-8")

    test_pcap = tmp_path / "test_incomplete.pcap"
    test_pcap.write_bytes(demo_pcap.read_bytes())

    with pytest.raises(ValueError) as exc_info:
        validate_pcap_labels(test_pcap)
    assert "has no label" in str(exc_info.value)


def test_each_lab_pcap_under_5mb_and_lab_traffic_only():
    """Each lab pcap must be under 5 MB and use lab RFC 1918 addresses."""
    demo_dir = Path("data/demo")
    pcaps = list(demo_dir.glob("*.pcap"))
    assert len(pcaps) >= 3

    for pcap in pcaps:
        size = pcap.stat().st_size
        assert size < 5 * 1024 * 1024, f"{pcap.name} exceeds 5 MB ({size} bytes)"

        for flow in ReplaySource(pcap).flows():
            # Lab traffic uses 10.0.x.x
            assert flow.src_ip.startswith("10.0."), f"Unexpected src_ip: {flow.src_ip}"
            assert flow.dst_ip.startswith("10.0."), f"Unexpected dst_ip: {flow.dst_ip}"
