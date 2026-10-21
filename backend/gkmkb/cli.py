import argparse
import sys

from backend.gkmkb.pipeline import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gkmkb")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="replay a pcap through the engine")
    replay.add_argument("pcap")
    replay.add_argument("--window", type=float, default=60.0, help="gate window in seconds")
    replay.add_argument("--threshold", type=float, default=0.7, help="gate score threshold")
    args = parser.parse_args(argv)

    result = run(args.pcap, window_seconds=args.window, threshold=args.threshold)
    print(f"flows: {result.flows}")
    print(f"detections: {len(result.detections)}")
    for d in result.detections:
        print(
            f"  {d.source:<10} {d.entity.src_ip} -> {d.entity.dst_ip}  "
            f"score={d.score:.2f}  {d.label}"
        )
    print(f"alerts: {len(result.alerts)}")
    for a in result.alerts:
        print(
            f"  ALERT {a.alert_id} {a.entity.src_ip} -> {a.entity.dst_ip}  "
            f"severity={a.severity}  detections={','.join(a.detection_ids)}"
        )
    if any("[stub]" in d.label for d in result.detections):
        print("note: FlowSight is a [stub] until the real detector lands; CoverTrace is real")
    return 0


if __name__ == "__main__":
    sys.exit(main())
