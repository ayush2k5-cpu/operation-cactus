import argparse
import sys

from backend.gkmkb.pipeline import run
from capture.replay import ReplayError


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
    uvicorn.run(create_app(store), host=settings.api_host, port=8000)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="gkmkb")
    sub = parser.add_subparsers(dest="command", required=True)
    replay = sub.add_parser("replay", help="replay a pcap through the engine")
    replay.add_argument("pcap")
    replay.add_argument("--window", type=float, default=None, help="gate window in seconds")
    replay.add_argument("--threshold", type=float, default=None, help="gate score threshold")
    replay.add_argument(
        "--engage",
        action="store_true",
        default=False,
        help="engage honeypot on alerts",
    )
    sub.add_parser("serve", help="start the API (127.0.0.1 unless API_HOST is set)")
    args = parser.parse_args(argv)

    if args.command == "serve":
        return serve()

    from backend.gkmkb.settings import load_settings

    settings = load_settings()
    engage_fn = None
    if args.engage or settings.honeypot_engage:
        from mimicnet.honeypot import engage

        engage_fn = engage

    try:
        result = run(
            args.pcap,
            window_seconds=args.window,
            threshold=args.threshold,
            engage_fn=engage_fn,
        )
    except (FileNotFoundError, ReplayError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"flows: {result.flows}")
    print(f"detections: {len(result.detections)}")
    for d in result.detections:
        print(
            f"  {d.source:<10} {d.entity.src_ip} -> {d.entity.dst_ip}  "
            f"score={d.score:.2f}  {d.label}"
        )
    print(f"alerts: {len(result.alerts)}")
    for a in result.alerts:
        extra = f"  status={a.status}" if a.status != "open" else ""
        if a.session_id:
            extra += f"  session_id={a.session_id}"
        print(
            f"  ALERT {a.alert_id} {a.entity.src_ip} -> {a.entity.dst_ip}  "
            f"severity={a.severity}  detections={','.join(a.detection_ids)}{extra}"
        )
    if result.session:
        s = result.session
        print(f"session: {s.session_id} service={s.service}")
        if s.mitre:
            print("mitre tags:")
            for tag in s.mitre:
                print(f"  {tag.technique_id} {tag.name}: {tag.evidence}")
    if result.rules:
        print("rules:")
        for r in result.rules:
            print(
                f"  RULE {r.rule_id} target={r.target} type={r.type} "
                f"status={r.status} match={r.match}"
            )
    if any("[stub]" in d.label for d in result.detections):
        print("note: a [stub] detector fired; its output is not a capability")
    return 0


if __name__ == "__main__":
    sys.exit(main())
