"""SSH-like fake shell for the MimicNet honeypot. Not SSH: no real login, no cryptography.

Standard library only. `engage` sends this file's source into the container with
`python -c`, so it must not import anything from the repo. Events are plain dicts
(ts, type, data); the host turns them into contract types.

When run as a program it plays the commands in GKMKB_SCRIPT (a JSON list) as the
attacker GKMKB_ATTACKER and prints one JSON event per line.
"""

import json
import os
from datetime import UTC, datetime

BANNER = "SSH-like service (lab honeypot, not SSH)"
TUNNEL_DOMAIN = "t.example.test"

# The scripted attacker: a fixed list the team plays. There is no real attacker.
SCRIPTED_ATTACKER = [
    "whoami",
    "uname -a",
    "cat /etc/passwd",
    f"iodine -f {TUNNEL_DOMAIN}",
    "exit",
]

CANNED = {
    "whoami": "root",
    "id": "uid=0(root) gid=0(root) groups=0(root)",
    "uname -a": "Linux lab-host 6.1.0 #1 SMP x86_64 GNU/Linux",
    "pwd": "/root",
    "ls": "notes.txt",
    "cat /etc/passwd": "root:x:0:0:root:/root:/bin/sh",
}
EXIT_WORDS = {"exit", "logout"}


class SshLikeShell:
    def __init__(self, attacker_addr: str, banner: str = BANNER):
        self.attacker_addr = attacker_addr
        self.banner = banner
        self.events: list[dict] = []

    def _log(self, type_: str, **data: str) -> None:
        self.events.append({"ts": datetime.now(UTC).isoformat(), "type": type_, "data": data})

    def connect(self) -> str:
        self._log("connect", attacker_addr=self.attacker_addr, banner=self.banner)
        return self.banner

    def feed(self, line: str) -> str | None:
        """Handle one typed line. Returns the reply, or None when the attacker leaves."""
        line = line.strip()
        if line in EXIT_WORDS:
            self._log("disconnect", reason=line)
            return None
        reply = CANNED.get(line, f"sh: {line.split()[0]}: command not found" if line else "")
        self._log("command", line=line, reply=reply)
        return reply

    def run(self, commands: list[str]) -> list[dict]:
        """Play the commands in order. Without an exit line the attacker just drops."""
        self.connect()
        for line in commands:
            if self.feed(line) is None:
                break
        else:
            self._log("disconnect", reason="end of script")
        return self.events


def main() -> None:
    shell = SshLikeShell(os.environ["GKMKB_ATTACKER"])
    for event in shell.run(json.loads(os.environ["GKMKB_SCRIPT"])):
        print(json.dumps(event), flush=True)


if __name__ == "__main__":
    main()
