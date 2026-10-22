import argparse
import sys

from backend.gkmkb.pipeline import run


def serve() -> int:
    import uvicorn

    from backend.gkmkb.api import create_app
    from backend.gkmkb.settings import load_settings
    from backend.gkmkb.storage import MemoryStore, MongoStore

    settings = load_settings()
    if settings.mongo_uri:
        store = MongoStore(settings.mongo_uri, settings.mongo_db)
    else:
        store = MemoryStore()
    uvicorn.run(create_app(store), host="127.0.0.1", port=8000)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gkmkb")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="replay a pcap through the engine")
    replay.add_argument("pcap")
    replay.add_argument("--window", type=float, default=None, help="gate window in seconds")
    replay.add_argument("--threshold", type=float, default=None, help="gate score threshold")
    sub.add_parser("serve", help="start the API on 127.0.0.1")
    args = parser.parse_args(argv)

    if args.command == "serve":
        return serve()

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
