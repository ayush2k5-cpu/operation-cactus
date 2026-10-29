"""Run the review demo by itself and print PASS or FAIL for each step.

  python scripts/demo.py                  check run: CLI, API and honeypot, then stop
  python scripts/demo.py --no-honeypot    skip the Docker honeypot step
  python scripts/demo.py --console        also start the Console, open it, and keep running

Steps follow docs/Review2Brief.md section 6. Uses the crafted pcaps in data/demo.
Needs the project virtualenv (run it with .venv python) and, for the honeypot, Docker running.
"""

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 8000
API = f"http://127.0.0.1:{PORT}"
CONSOLE = "http://localhost:5173"
TUNNEL = "dns_tunnel_plus_benign.pcap"
CONTROL = "single_signal_control.pcap"
HARD = "hard_benign_dns.pcap"

results: list[tuple[bool, str]] = []


def check(ok: bool, text: str) -> None:
    results.append((ok, text))
    print(f"  {'PASS' if ok else 'FAIL'}  {text}")


def step(title: str) -> None:
    print(f"\n{title}")


def cli(*args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-m", "backend.gkmkb.cli", *args]
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")


def alerts_in(output: str) -> int | None:
    found = re.search(r"^alerts: (\d+)", output, re.M)
    return int(found.group(1)) if found else None


def api(path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(API + path, data=data)
    if data:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)


def port_in_use() -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", PORT)) == 0


def docker_running() -> bool:
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "info"], capture_output=True).returncode == 0


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.terminate()


def wait_for(test, seconds: float, pause: float = 0.5):
    end = time.time() + seconds
    while time.time() < end:
        value = test()
        if value:
            return value
        time.sleep(pause)
    return None


def start_backend(honeypot: bool, delay_ms: int) -> subprocess.Popen:
    env = {
        **os.environ,
        "DATA_DIR": "data/demo",
        "REPLAY_EVENT_DELAY_MS": str(delay_ms),
        "HONEYPOT_ENGAGE": "1" if honeypot else "0",
    }
    cmd = [sys.executable, "-m", "backend.gkmkb.cli", "serve"]
    return subprocess.Popen(
        cmd, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def replay(pcap: str) -> tuple[dict, list]:
    replay_id = api("/api/replay", {"pcap": pcap})["replay_id"]
    finished = wait_for(
        lambda: next(
            (
                r
                for r in api("/api/replays")
                if r["replay_id"] == replay_id and r["state"] != "running"
            ),
            None,
        ),
        60,
    )
    return finished or {}, api(f"/api/alerts?replay_id={replay_id}")


def cli_steps() -> None:
    step("1. Command-line replay of the three demo pcaps")
    for pcap, expected in ((TUNNEL, 1), (CONTROL, 0), (HARD, 0)):
        out = cli("replay", str(Path("data/demo") / pcap))
        check(alerts_in(out.stdout) == expected, f"{pcap}: {expected} Alert(s)")
    with tempfile.TemporaryDirectory() as tmp:
        junk = Path(tmp) / "junk.pcap"
        junk.write_bytes(b"this is not a pcap")
        out = cli("replay", str(junk))
        check(
            out.returncode == 2 and "junk.pcap" in out.stderr,
            "a file that is not a pcap fails with exit 2",
        )


def api_steps(honeypot: bool) -> None:
    step("2. Replays through the backend API (what the Console does)")
    done, alerts = replay(TUNNEL)
    check(done.get("state") == "done" and len(alerts) == 1, f"{TUNNEL}: done, 1 Alert")
    check(done.get("detection_count") == 2, f"{TUNNEL}: 2 Detections (FlowSight and CoverTrace)")
    if honeypot and alerts:
        engaged = wait_for(
            lambda: next(
                (
                    a
                    for a in api("/api/alerts")
                    if a["alert_id"] == alerts[0]["alert_id"] and a["status"] == "engaged"
                ),
                None,
            ),
            90,
            1,
        )
        check(bool(engaged), "the Alert starts a honeypot session (status engaged)")
        if engaged:
            session = api(f"/api/sessions/{engaged['session_id']}")
            lines = [e["data"].get("line", "") for e in session["events"] if e["type"] == "command"]
            attacker = next(
                (
                    e["data"].get("attacker_addr")
                    for e in session["events"]
                    if e["type"] == "connect"
                ),
                None,
            )
            print(f"        attacker {attacker}; commands: {', '.join(lines)}")
            check(
                any("iodine" in line for line in lines), "the session recorded the tunnel command"
            )
    done, alerts = replay(CONTROL)
    check(done.get("state") == "done" and alerts == [], f"{CONTROL}: done, 0 Alerts")
    done, alerts = replay(HARD)
    check(
        done.get("detection_count") == 1 and alerts == [],
        f"{HARD}: FlowSight alone flags it, the gate raises 0 Alerts",
    )


def eval_step() -> None:
    step("3. Evaluation on the crafted pcaps (synthetic data)")
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(
            [sys.executable, "-m", "eval", "--output-file", str(Path(tmp) / "r.csv")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
    rows = [
        line for line in out.stdout.splitlines() if re.match(r"(covertrace|flowsight|gate)\b", line)
    ]
    for row in rows:
        print("        " + row.strip())
    check(len(rows) == 3, "metrics table for CoverTrace, FlowSight and the gate")


def run_console(proc: subprocess.Popen) -> None:
    npm = shutil.which("npm")
    if not npm or not (ROOT / "dashboard" / "node_modules").exists():
        print("\nConsole not started: run `npm --prefix dashboard ci` once first.")
        return
    console = subprocess.Popen(
        [npm, "--prefix", "dashboard", "run", "dev", "--", "--port", "5173", "--strictPort"],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(4)
        print(f"\nConsole: {CONSOLE}  (backend {API}). Press Ctrl+C to stop both.")
        webbrowser.open(CONSOLE)
        while proc.poll() is None and console.poll() is None:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        stop(console)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-honeypot", action="store_true", help="skip the Docker honeypot step")
    parser.add_argument("--console", action="store_true", help="start the Console and keep running")
    args = parser.parse_args()

    if port_in_use():
        sys.exit(f"Port {PORT} is already in use. Stop the other backend first.")

    honeypot = not args.no_honeypot and docker_running()
    if not args.no_honeypot and not honeypot:
        print("Docker is not running: the honeypot step is skipped.")

    cli_steps()
    backend = start_backend(honeypot, delay_ms=0)
    try:
        if not wait_for(lambda: _healthy(), 30):
            check(False, "the backend starts")
        else:
            api_steps(honeypot)
        eval_step()
        if args.console:
            stop(backend)
            time.sleep(1)
            backend = start_backend(honeypot, delay_ms=400)
            if wait_for(lambda: _healthy(), 30):
                run_console(backend)
    finally:
        stop(backend)

    failed = [text for ok, text in results if not ok]
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


def _healthy() -> bool:
    try:
        return api("/api/health").get("status") == "ok"
    except (urllib.error.URLError, OSError):
        return False


if __name__ == "__main__":
    sys.exit(main())
