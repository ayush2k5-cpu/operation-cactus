"""Tests for the evaluation runner (ticket #84).

Covers all acceptance criteria:
- One command prints a metrics table per detector and for the gate, with raw counts
- Crafted results and real results are written to separate files
- Tuning and test sets share no capture
- The same seed gives byte-identical output
- A missing labels file fails with a clear message
- Time to first Detection is recorded for each tunnel Entity
"""

from pathlib import Path

import pytest

from eval.labels import find_labels_file, load_labels
from eval.runner import (
    EVAL_TARGETS,
    default_crafted_pcaps,
    evaluate_pcaps,
    main,
    split_captures,
    write_results_csv,
)

DEMO_PCAP = Path("data/demo/dns_tunnel_plus_benign.pcap")
DEMO_LABELS = Path("data/demo/dns_tunnel_plus_benign.labels")
CONTROL_PCAP = Path("data/demo/single_signal_control.pcap")
CONTROL_LABELS = Path("data/demo/single_signal_control.labels")


def test_missing_labels_file_fails_with_clear_message(tmp_path):
    pcap_without_labels = tmp_path / "orphan.pcap"
    pcap_without_labels.write_bytes(b"fake pcap content")

    with pytest.raises(FileNotFoundError) as exc_info:
        find_labels_file(pcap_without_labels)

    msg = str(exc_info.value)
    assert "Missing labels file for pcap" in msg
    assert "orphan.pcap" in msg
    assert "expected labels file" in msg


def test_labels_file_parser(tmp_path):
    lab_file = tmp_path / "sample.labels"
    lab_file.write_text(
        "# Comment line\n"
        "src_ip,dst_ip,label\n"
        "10.0.1.10,10.0.0.53,benign\n"
        "10.0.2.20,10.0.0.53,tunnel\n",
        encoding="utf-8",
    )
    labels = load_labels(lab_file)
    assert labels[("10.0.1.10", "10.0.0.53")] == "benign"
    assert labels[("10.0.2.20", "10.0.0.53")] == "tunnel"


def test_labels_file_invalid_label_raises(tmp_path):
    lab_file = tmp_path / "bad.labels"
    lab_file.write_text("10.0.1.10,10.0.0.53,unknown\n", encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        load_labels(lab_file)
    assert "must be 'tunnel' or 'benign'" in str(exc.value)


def test_tuning_and_test_sets_share_no_capture():
    captures = [Path(f"cap_{i}.pcap") for i in range(10)]
    tune, test = split_captures(captures, seed=42, tune_ratio=0.5)

    assert len(tune) == 5
    assert len(test) == 5
    # Sets share no capture
    assert set(tune).isdisjoint(set(test))
    # All captures preserved
    assert set(tune) | set(test) == set(captures)


@pytest.mark.skipif(not DEMO_PCAP.exists(), reason="demo pcap not generated")
def test_evaluation_runner_prints_table_per_detector_and_gate_with_raw_counts(capsys):
    ret = main(["--pcap", str(DEMO_PCAP)])
    assert ret == 0
    out = capsys.readouterr().out

    # Header and synthetic indicator
    assert "GKMKB Evaluation Results" in out
    assert "SYNTHETIC" in out
    assert "Hits" in out and "Misses" in out and "FalseAlarms" in out

    # Contains every target
    for target in EVAL_TARGETS:
        assert target in out

    # Raw counts displayed beside percentages (e.g. 1/1, 0/1)
    assert "(1/1)" in out
    assert "(0/1)" in out

    # FlowSight marked with [stub]
    assert "flowsight" in out


@pytest.mark.skipif(not DEMO_PCAP.exists(), reason="demo pcap not generated")
def test_time_to_first_detection_recorded_for_tunnel_entity(capsys):
    ret = main(["--pcap", str(DEMO_PCAP)])
    assert ret == 0
    out = capsys.readouterr().out

    assert "Time to first Detection (tunnel entities):" in out
    assert "10.0.2.20 -> 10.0.0.53" in out
    assert "covertrace" in out
    assert "flowsight" in out
    assert "gate" in out


def test_crafted_and_real_results_written_to_separate_files(tmp_path):
    crafted_res = evaluate_pcaps([DEMO_PCAP], dataset_type="crafted", seed=42)
    real_res = evaluate_pcaps([DEMO_PCAP], dataset_type="real", seed=42)

    crafted_csv = tmp_path / "crafted_results.csv"
    real_csv = tmp_path / "real_results.csv"

    write_results_csv(crafted_res, crafted_csv)
    write_results_csv(real_res, real_csv)

    assert crafted_csv.exists()
    assert real_csv.exists()
    assert crafted_csv != real_csv

    crafted_text = crafted_csv.read_text(encoding="utf-8")
    real_text = real_csv.read_text(encoding="utf-8")

    # Crafted file explicitly says synthetic
    assert "crafted,synthetic" in crafted_text
    assert "real,real" in real_text


def test_same_seed_gives_byte_identical_output(tmp_path):
    res1 = evaluate_pcaps([DEMO_PCAP], dataset_type="crafted", seed=42)
    res2 = evaluate_pcaps([DEMO_PCAP], dataset_type="crafted", seed=42)

    f1 = tmp_path / "run1.csv"
    f2 = tmp_path / "run2.csv"

    write_results_csv(res1, f1)
    write_results_csv(res2, f2)

    assert f1.read_bytes() == f2.read_bytes()


def test_default_crafted_pcaps_found():
    pcaps = default_crafted_pcaps()
    assert len(pcaps) >= 1
    assert any("dns_tunnel_plus_benign" in str(p) for p in pcaps)
