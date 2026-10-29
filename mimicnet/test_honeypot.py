import json
from datetime import UTC, datetime

import pytest

from contracts.models import Alert, Entity
from mimicnet.honeypot import EngageBusy, EngageError, Settings, engage, play
from mimicnet.shell import SCRIPTED_ATTACKER, TUNNEL_DOMAIN, SshLikeShell

ALERT = Alert(
    alert_id="alert-1",
    entity=Entity(src_ip="10.0.2.20", dst_ip="10.0.2.53"),
    detection_ids=["d1", "d2"],
    severity="high",
    ts=datetime(2026, 10, 21, tzinfo=UTC),
    status="open",
)


def test_scripted_attacker_gives_ordered_session():
    session = play("alert-1")
    kinds = [e.type for e in session.events]
    assert kinds == ["connect"] + ["command"] * 4 + ["disconnect"]
    assert session.events[0].data["attacker_addr"] == Settings().attacker_addr
    lines = [e.data["line"] for e in session.events if e.type == "command"]
    assert lines == SCRIPTED_ATTACKER[:-1]
    assert any(TUNNEL_DOMAIN in line for line in lines)
    assert session.service == "ssh-like"
    assert session.ended == session.events[-1].ts


def test_script_without_exit_still_ends():
    events = SshLikeShell("192.0.2.9").run(["whoami"])
    assert events[-1]["type"] == "disconnect"


def test_unknown_command_gets_not_found():
    events = SshLikeShell("192.0.2.9").run(["frobnicate now"])
    assert events[1]["data"]["reply"] == "sh: frobnicate: command not found"


class FakeContainer:
    id = "fake-container"

    def __init__(self, owner, wait_error=None, status=0):
        self.owner = owner
        self.wait_error = wait_error
        self.status = status
        self.removed = False
        self.killed = False

    def start(self):
        pass

    def wait(self, timeout):
        self.owner.wait_timeout = timeout
        if self.wait_error:
            raise self.wait_error
        return {"StatusCode": self.status}

    def kill(self):
        self.killed = True

    def logs(self, stdout=True, stderr=False):
        events = SshLikeShell("192.0.2.50").run(["whoami", "exit"])
        return "\n".join(json.dumps(e) for e in events).encode()

    def remove(self, force=False):
        self.removed = True


class FakeClient:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.container = None
        self.containers = self
        self.created = 0

    def create(self, image, command, **opts):
        self.created += 1
        self.opts = opts
        self.container = FakeContainer(self, **self.kwargs)
        return self.container


def test_engage_container_settings():
    client = FakeClient()
    session = engage(ALERT, client=client)
    opts = client.opts
    assert client.created == 1
    assert opts["network_mode"] == "none"
    assert "volumes" not in opts and "binds" not in opts
    assert opts["mem_limit"] == "128m"
    assert opts["nano_cpus"] == int(0.5e9)
    assert client.wait_timeout == 120
    assert client.container.removed
    assert [e.type for e in session.events] == ["connect", "command", "disconnect"]
    assert session.container_id == "fake-container"
    assert session.alert_id == "alert-1"


def test_container_removed_after_error():
    client = FakeClient(status=1)
    with pytest.raises(EngageError):
        engage(ALERT, client=client)
    assert client.container.removed


def test_timeout_kills_and_adds_timeout_event():
    client = FakeClient(wait_error=TimeoutError())
    session = engage(ALERT, client=client)
    assert client.container.killed and client.container.removed
    assert session.events[-1].type == "timeout"


def test_second_engage_refused_while_one_runs():
    client = FakeClient()
    inner = {}
    real_wait = FakeContainer.wait

    def wait_and_try_again(self, timeout):
        with pytest.raises(EngageBusy, match="already running"):
            engage(ALERT, client=FakeClient())
        inner["refused"] = True
        return real_wait(self, timeout)

    FakeContainer.wait = wait_and_try_again
    try:
        engage(ALERT, client=client)
    finally:
        FakeContainer.wait = real_wait
    assert inner["refused"]
    engage(ALERT, client=FakeClient())


def _docker_client():
    docker = pytest.importorskip("docker")
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception:
        pytest.skip("Docker is not available")


@pytest.mark.docker
def test_engage_real_container_is_removed():
    client = _docker_client()
    session = engage(ALERT, client=client)
    assert [e.type for e in session.events][0] == "connect"
    assert session.events[-1].type == "disconnect"
    assert any(TUNNEL_DOMAIN in e.data.get("line", "") for e in session.events)
    from docker.errors import NotFound

    with pytest.raises(NotFound):
        client.containers.get(session.container_id)
