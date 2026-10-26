"""Honeypot session and `engage`: one isolated Docker container running the SSH-like shell.

The container has no network at all, so the scripted attacker's commands go in as an
environment variable and the shell prints its events as JSON lines to the container logs.
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from contracts.models import Alert, HoneypotSession, SessionEvent
from mimicnet.shell import SCRIPTED_ATTACKER, SshLikeShell

SERVICE = "ssh-like"
SHELL_SOURCE = Path(__file__).with_name("shell.py")


class EngageBusy(RuntimeError):
    """A honeypot is already running; only one at a time."""


class EngageError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    image: str = field(default_factory=lambda: os.getenv("HONEYPOT_IMAGE", "python:3.12-slim"))
    memory: str = field(default_factory=lambda: os.getenv("HONEYPOT_MEMORY", "128m"))
    cpus: float = field(default_factory=lambda: float(os.getenv("HONEYPOT_CPUS", "0.5")))
    max_life_s: int = field(default_factory=lambda: int(os.getenv("HONEYPOT_MAX_LIFE_S", "120")))
    attacker_addr: str = field(
        default_factory=lambda: os.getenv("HONEYPOT_ATTACKER_ADDR", "192.0.2.50")
    )


_running = threading.Lock()


def _is_timeout(exc: Exception) -> bool:
    """docker-py raises a requests error when `wait` times out; requests ships with docker."""
    if isinstance(exc, TimeoutError):
        return True
    try:
        import requests
    except ImportError:
        return False
    return isinstance(exc, requests.exceptions.RequestException)


def _session(alert_id: str, container_id: str, started: datetime, events: list[dict]):
    parsed = [SessionEvent(**e) for e in events]
    return HoneypotSession(
        session_id=f"session-{uuid.uuid4().hex[:8]}",
        alert_id=alert_id,
        service=SERVICE,
        container_id=container_id,
        started=started,
        ended=parsed[-1].ts if parsed else None,
        events=parsed,
    )


def play(alert_id: str, commands: list[str] = SCRIPTED_ATTACKER, settings: Settings | None = None):
    """Run the commands against the shell in this process. No Docker."""
    settings = settings or Settings()
    started = datetime.now(UTC)
    events = SshLikeShell(settings.attacker_addr).run(commands)
    return _session(alert_id, "in-process", started, events)


def engage(
    alert: Alert,
    commands: list[str] = SCRIPTED_ATTACKER,
    settings: Settings | None = None,
    client: Any = None,
) -> HoneypotSession:
    """Run the shell in one container, read its events from the logs, remove the container."""
    settings = settings or Settings()
    if not _running.acquire(blocking=False):
        raise EngageBusy("a honeypot session is already running; engage refused")
    try:
        if client is None:
            import docker

            client = docker.from_env()
        started = datetime.now(UTC)
        container = client.containers.create(
            settings.image,
            ["python", "-c", SHELL_SOURCE.read_text(encoding="utf-8")],
            environment={
                "GKMKB_ATTACKER": settings.attacker_addr,
                "GKMKB_SCRIPT": json.dumps(commands),
            },
            network_mode="none",
            mem_limit=settings.memory,
            nano_cpus=int(settings.cpus * 1e9),
            read_only=True,
            cap_drop=["ALL"],
            labels={"gkmkb": "mimicnet-honeypot"},
        )
        try:
            container.start()
            timed_out = False
            try:
                result = container.wait(timeout=settings.max_life_s)
            except Exception as exc:
                if not _is_timeout(exc):
                    raise
                timed_out = True
                container.kill()
                result = {"StatusCode": 0}
            if result.get("StatusCode"):
                tail = container.logs(stderr=True).decode(errors="replace")[-500:]
                raise EngageError(f"honeypot container failed: {tail}")
            logs = container.logs(stdout=True, stderr=False).decode(errors="replace")
            events = [json.loads(line) for line in logs.splitlines() if line.startswith("{")]
            if timed_out:
                events.append(
                    {
                        "ts": datetime.now(UTC).isoformat(),
                        "type": "timeout",
                        "data": {"max_life_s": str(settings.max_life_s)},
                    }
                )
            return _session(alert.alert_id, container.id, started, events)
        finally:
            container.remove(force=True)
    finally:
        _running.release()
