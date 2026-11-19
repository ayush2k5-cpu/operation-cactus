"""Rules extraction from Honeypot sessions.

Reads a HoneypotSession and returns proposed detection Rules targeting CoverTrace:
- Suffix rule: extracted from tunnel command text in command events (e.g. iodine -f domain)
- Address rule: extracted from attacker_addr in the connect event

Both target CoverTrace, have type 'ioc', and are born with status 'proposed'.
A session without a tunnel command yields only the address rule.
"""

import re

from contracts.models import HoneypotSession, Rule

_TUNNEL_PATTERNS = [
    re.compile(r"\biodine\s+(?:-[a-zA-Z0-9]+\s+)*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", re.IGNORECASE),
    re.compile(
        r"\bdnscat2?\s+.*?(?:--dns\s+domain=)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b", re.IGNORECASE
    ),
]


def _extract_tunnel_domain(command_line: str) -> str | None:
    line = command_line.strip()
    for pat in _TUNNEL_PATTERNS:
        m = pat.search(line)
        if m:
            domain = m.group(1).strip().strip(".")
            if "." in domain and not domain.startswith("-"):
                return domain.lower()
    return None


def rules_from(session: HoneypotSession) -> list[Rule]:
    """Extract proposed IoC rules from a honeypot session for CoverTrace.

    Reads only the session events. Produces a suffix rule from any tunnel command
    line and an address rule from the connect event. If no tunnel command is found,
    only the address rule is proposed.
    """
    rules: list[Rule] = []
    attacker_addr: str | None = None
    tunnel_domain: str | None = None

    for event in session.events:
        if event.type == "connect":
            addr = event.data.get("attacker_addr") or event.data.get("src")
            if addr and not attacker_addr:
                attacker_addr = addr.strip()
        elif event.type == "command":
            line = event.data.get("line", "")
            if not tunnel_domain:
                domain = _extract_tunnel_domain(line)
                if domain:
                    tunnel_domain = domain

    # Suffix rule
    if tunnel_domain:
        rules.append(
            Rule(
                rule_id=f"rule-{session.session_id}-suffix",
                target="covertrace",
                type="ioc",
                match={"qname_suffix": tunnel_domain},
                session_id=session.session_id,
                status="proposed",
            )
        )

    # Address rule
    if attacker_addr:
        rules.append(
            Rule(
                rule_id=f"rule-{session.session_id}-addr",
                target="covertrace",
                type="ioc",
                match={"src_ip": attacker_addr},
                session_id=session.session_id,
                status="proposed",
            )
        )

    return rules
