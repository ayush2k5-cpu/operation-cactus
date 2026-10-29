"""Evaluation runner for GKMKB on labelled pcaps.

Replays labelled pcaps through the real detectors and the gate by the same replay path
the CLI uses, counts hits, misses and false alarms per Entity episode, records time to
first Detection for each tunnel Entity, prints a metrics table with raw counts, and writes
seeded CSV files. Crafted results and real results are written to separate files.
"""

import argparse
import csv
import io
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from backend.gkmkb.pipeline import run as replay_pipeline
from capture.replay import ReplaySource
from eval.labels import find_labels_file, load_labels
from eval.metrics import (
    MetricRatio,
    f1,
    false_alarm_rate,
    false_alarms,
    hits,
    misses,
    precision,
    recall,
    true_negatives,
)

TARGET_COVERTRACE = "covertrace"
TARGET_FLOWSIGHT = "flowsight"
TARGET_GATE = "gate"
EVAL_TARGETS = [TARGET_COVERTRACE, TARGET_FLOWSIGHT, TARGET_GATE]


@dataclass
class EntityOutcome:
    pcap_name: str
    entity: tuple[str, str]
    true_label: str  # "tunnel" or "benign"
    detected: dict[str, bool] = field(default_factory=dict)
    scores: dict[str, float] = field(default_factory=dict)
    first_detection_seconds: dict[str, float | None] = field(default_factory=dict)


@dataclass
class TargetMetrics:
    target: str
    hits: int
    misses: int
    false_alarms: int
    true_negatives: int
    precision: MetricRatio
    recall: MetricRatio
    f1: MetricRatio
    false_alarm_rate: MetricRatio
    tunnel_first_detection_seconds: dict[tuple[str, str], float | None] = field(
        default_factory=dict
    )


@dataclass
class EvaluationResult:
    dataset_type: str  # "crafted" or "real"
    data_label: str  # "synthetic" for crafted, "real" for real
    seed: int
    targets: dict[str, TargetMetrics] = field(default_factory=dict)
    outcomes: list[EntityOutcome] = field(default_factory=list)


def get_capture_start(pcap: Path) -> datetime | None:
    """Return the start timestamp of the first flow in the pcap."""
    for flow in ReplaySource(pcap).flows():
        return flow.start_ts
    return None


def split_captures(
    captures: list[Path], seed: int = 42, tune_ratio: float = 0.5
) -> tuple[list[Path], list[Path]]:
    """Split captures into tuning and held-out test sets by capture (never by window).

    Guarantees that tuning and test sets share no capture.
    """
    sorted_caps = sorted(captures)
    rng = random.Random(seed)
    shuffled = sorted_caps.copy()
    rng.shuffle(shuffled)

    cutoff = int(len(shuffled) * tune_ratio)
    tuning_set = sorted(shuffled[:cutoff])
    test_set = sorted(shuffled[cutoff:])
    return tuning_set, test_set


def evaluate_pcaps(
    pcaps: list[Path],
    dataset_type: str = "crafted",
    seed: int = 42,
    window_seconds: float = 60.0,
    threshold: float = 0.7,
) -> EvaluationResult:
    """Replay each labelled pcap and compute per-Entity outcomes and metrics."""
    data_label = "synthetic" if dataset_type == "crafted" else "real"
    outcomes: list[EntityOutcome] = []

    # Sort pcaps deterministically
    for pcap in sorted(pcaps):
        labels_file = find_labels_file(pcap)
        labels = load_labels(labels_file)
        capture_start = get_capture_start(pcap)

        # Replay through the same path the CLI uses
        result = replay_pipeline(pcap, window_seconds=window_seconds, threshold=threshold)

        # Index detections by entity and source
        dets_by_entity: dict[tuple[str, str], dict[str, list]] = defaultdict(
            lambda: {"flowsight": [], "covertrace": []}
        )
        for d in result.detections:
            key = (d.entity.src_ip, d.entity.dst_ip)
            dets_by_entity[key][d.source].append(d)

        alerts_by_entity: dict[tuple[str, str], list] = defaultdict(list)
        for a in result.alerts:
            key = (a.entity.src_ip, a.entity.dst_ip)
            alerts_by_entity[key].append(a)

        for entity, true_label in sorted(labels.items()):
            det_map: dict[str, bool] = {}
            score_map: dict[str, float] = {}
            time_map: dict[str, float | None] = {}

            # CoverTrace
            ct_dets = dets_by_entity[entity]["covertrace"]
            det_map[TARGET_COVERTRACE] = len(ct_dets) > 0
            score_map[TARGET_COVERTRACE] = max((d.score for d in ct_dets), default=0.0)
            if ct_dets and capture_start:
                first_ts = min(d.ts for d in ct_dets)
                time_map[TARGET_COVERTRACE] = round((first_ts - capture_start).total_seconds(), 4)
            else:
                time_map[TARGET_COVERTRACE] = None

            # FlowSight stub
            fs_dets = dets_by_entity[entity]["flowsight"]
            det_map[TARGET_FLOWSIGHT] = len(fs_dets) > 0
            score_map[TARGET_FLOWSIGHT] = max((d.score for d in fs_dets), default=0.0)
            if fs_dets and capture_start:
                first_ts = min(d.ts for d in fs_dets)
                time_map[TARGET_FLOWSIGHT] = round((first_ts - capture_start).total_seconds(), 4)
            else:
                time_map[TARGET_FLOWSIGHT] = None

            # Gate
            g_alerts = alerts_by_entity[entity]
            det_map[TARGET_GATE] = len(g_alerts) > 0
            score_map[TARGET_GATE] = 1.0 if g_alerts else 0.0
            if g_alerts and capture_start:
                first_ts = min(a.ts for a in g_alerts)
                time_map[TARGET_GATE] = round((first_ts - capture_start).total_seconds(), 4)
            else:
                time_map[TARGET_GATE] = None

            outcomes.append(
                EntityOutcome(
                    pcap_name=pcap.name,
                    entity=entity,
                    true_label=true_label,
                    detected=det_map,
                    scores=score_map,
                    first_detection_seconds=time_map,
                )
            )

    # Calculate metrics per target
    target_metrics: dict[str, TargetMetrics] = {}
    for target in EVAL_TARGETS:
        y_true = [1 if oc.true_label == "tunnel" else 0 for oc in outcomes]
        y_pred = [1 if oc.detected[target] else 0 for oc in outcomes]

        tunnel_first_times = {
            oc.entity: oc.first_detection_seconds[target]
            for oc in outcomes
            if oc.true_label == "tunnel"
        }

        target_metrics[target] = TargetMetrics(
            target=target,
            hits=hits(y_true, y_pred),
            misses=misses(y_true, y_pred),
            false_alarms=false_alarms(y_true, y_pred),
            true_negatives=true_negatives(y_true, y_pred),
            precision=precision(y_true, y_pred),
            recall=recall(y_true, y_pred),
            f1=f1(y_true, y_pred),
            false_alarm_rate=false_alarm_rate(y_true, y_pred),
            tunnel_first_detection_seconds=tunnel_first_times,
        )

    return EvaluationResult(
        dataset_type=dataset_type,
        data_label=data_label,
        seed=seed,
        targets=target_metrics,
        outcomes=outcomes,
    )


def format_ratio(mr: MetricRatio) -> str:
    """Format a metric ratio with its decimal value and raw numerator/denominator."""
    if mr.ratio is None:
        return f"n/a ({mr.numerator}/{mr.denominator})"
    return f"{mr.ratio:.4f} ({mr.numerator}/{mr.denominator})"


def print_metrics_table(result: EvaluationResult, out_stream=None) -> None:
    """Print formatted metrics table per detector and for the gate, with raw counts."""
    if out_stream is None:
        out_stream = sys.stdout
    label_tag = f"{result.data_label.upper()} ({result.dataset_type} pcaps)"
    print("=" * 86, file=out_stream)
    print(f"GKMKB Evaluation Results -- {label_tag}", file=out_stream)
    print(f"Seed: {result.seed} | Per-Entity episode evaluation", file=out_stream)
    print("=" * 86, file=out_stream)

    header = (
        f"{'Target':<18} {'Hits':>5} {'Misses':>6} {'FalseAlarms':>11} {'TrueNeg':>8} "
        f"{'Precision':<14} {'Recall':<14} {'F1':<14} {'FAR':<14}"
    )
    print(header, file=out_stream)
    print("-" * 86, file=out_stream)

    for target in EVAL_TARGETS:
        tm = result.targets[target]
        print(
            f"{tm.target:<18} "
            f"{tm.hits:>5} "
            f"{tm.misses:>6} "
            f"{tm.false_alarms:>11} "
            f"{tm.true_negatives:>8} "
            f"{format_ratio(tm.precision):<14} "
            f"{format_ratio(tm.recall):<14} "
            f"{format_ratio(tm.f1):<14} "
            f"{format_ratio(tm.false_alarm_rate):<14}",
            file=out_stream,
        )

    print("-" * 86, file=out_stream)
    print("Time to first Detection (tunnel entities):", file=out_stream)
    tunnel_outcomes = [oc for oc in result.outcomes if oc.true_label == "tunnel"]
    if not tunnel_outcomes:
        print("  (no tunnel entities present)", file=out_stream)
    else:
        for oc in tunnel_outcomes:
            src, dst = oc.entity
            print(f"  Entity {src} -> {dst} in {oc.pcap_name}:", file=out_stream)
            for target in EVAL_TARGETS:
                t_sec = oc.first_detection_seconds[target]
                t_str = f"{t_sec:.2f}s" if t_sec is not None else "not detected"
                print(f"    {target:<18}: {t_str}", file=out_stream)

    print("=" * 86, file=out_stream)
    if result.dataset_type == "crafted":
        print(
            "Note: output is synthetic; lab pcaps only, never presented as real.",
            file=out_stream,
        )


def write_results_csv(result: EvaluationResult, output_path: Path) -> None:
    """Write evaluation metrics to a CSV file.

    Crafted results and real results are written to separate files, and the output
    is deterministically formatted so identical seeds produce byte-identical output.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")

    writer.writerow(
        [
            "dataset_type",
            "data_label",
            "seed",
            "target",
            "hits",
            "misses",
            "false_alarms",
            "true_negatives",
            "precision",
            "precision_raw",
            "recall",
            "recall_raw",
            "f1",
            "f1_raw",
            "false_alarm_rate",
            "false_alarm_rate_raw",
            "time_to_first_detection_mean_s",
        ]
    )

    for target in EVAL_TARGETS:
        tm = result.targets[target]
        valid_times = [t for t in tm.tunnel_first_detection_seconds.values() if t is not None]
        mean_time_str = f"{sum(valid_times) / len(valid_times):.4f}" if valid_times else ""

        prec_str = f"{tm.precision.ratio:.4f}" if tm.precision.ratio is not None else ""
        rec_str = f"{tm.recall.ratio:.4f}" if tm.recall.ratio is not None else ""
        f1_str = f"{tm.f1.ratio:.4f}" if tm.f1.ratio is not None else ""
        far_str = (
            f"{tm.false_alarm_rate.ratio:.4f}" if tm.false_alarm_rate.ratio is not None else ""
        )

        writer.writerow(
            [
                result.dataset_type,
                result.data_label,
                result.seed,
                tm.target,
                tm.hits,
                tm.misses,
                tm.false_alarms,
                tm.true_negatives,
                prec_str,
                f"{tm.precision.numerator}/{tm.precision.denominator}",
                rec_str,
                f"{tm.recall.numerator}/{tm.recall.denominator}",
                f1_str,
                f"{tm.f1.numerator}/{tm.f1.denominator}",
                far_str,
                f"{tm.false_alarm_rate.numerator}/{tm.false_alarm_rate.denominator}",
                mean_time_str,
            ]
        )

    output_path.write_text(buf.getvalue(), encoding="utf-8")


def default_crafted_pcaps() -> list[Path]:
    """Find default crafted lab pcaps in data/demo and data/eval."""
    pcaps: list[Path] = []
    for rel_dir in ("data/demo", "data/eval"):
        d = Path(rel_dir)
        if d.is_dir():
            for p in d.glob("*.pcap"):
                # Only include pcaps that have a labels file beside them
                try:
                    find_labels_file(p)
                    pcaps.append(p)
                except FileNotFoundError:
                    continue
    return sorted(pcaps)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for the evaluation runner."""
    parser = argparse.ArgumentParser(
        prog="eval",
        description="GKMKB evaluation runner: evaluate detectors and gate on labelled pcaps",
    )
    parser.add_argument("--pcap", type=Path, help="single labelled pcap file to evaluate")
    parser.add_argument(
        "--pcap-dir", type=Path, help="directory containing labelled pcaps to evaluate"
    )
    parser.add_argument(
        "--dataset-type",
        choices=["crafted", "real"],
        default="crafted",
        help="dataset type: 'crafted' (synthetic, v1) or 'real'",
    )
    parser.add_argument("--seed", type=int, default=42, help="random seed for reproducibility")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("eval/results"),
        help="directory to write CSV results",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=None,
        help="explicit path to output CSV file (overrides output-dir)",
    )
    parser.add_argument(
        "--window", type=float, default=60.0, help="window in seconds for detectors and gate"
    )
    parser.add_argument("--threshold", type=float, default=0.7, help="score threshold for the gate")
    args = parser.parse_args(argv)

    if args.pcap:
        pcaps = [args.pcap]
    elif args.pcap_dir:
        pcaps = sorted(args.pcap_dir.glob("*.pcap"))
        if not pcaps:
            sys.exit(f"No pcaps found in directory: {args.pcap_dir}")
    else:
        pcaps = default_crafted_pcaps()
        if not pcaps:
            sys.exit(
                "No labelled crafted pcaps found in data/demo or data/eval. "
                "Specify --pcap or --pcap-dir."
            )

    result = evaluate_pcaps(
        pcaps=pcaps,
        dataset_type=args.dataset_type,
        seed=args.seed,
        window_seconds=args.window,
        threshold=args.threshold,
    )

    print_metrics_table(result)

    if args.output_file:
        out_file = args.output_file
    else:
        filename = "crafted_results.csv" if args.dataset_type == "crafted" else "real_results.csv"
        out_file = args.output_dir / filename

    write_results_csv(result, out_file)
    print(f"Results written to: {out_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
