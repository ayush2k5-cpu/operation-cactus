"""Tests for the MITRE keyword table and tagging function (ticket #85).

Acceptance criteria:
- Each row has technique_id, name, keyword, evidence_template, source_url and verified_date
- An exact-match test on the scripted attacker session
- A test that an unknown command gives no tag
- A test that every row has all required fields
- A row without verified_date is marked Unverified in the output
"""

from datetime import UTC, datetime

from contracts.models import MitreTag, SessionEvent
from eval.mitre import MITRE_TABLE, UNVERIFIED, MitreRow, _verification_label, tag_events
from mimicnet.shell import SCRIPTED_ATTACKER, SshLikeShell


def _make_event(line: str) -> SessionEvent:
    return SessionEvent(
        ts=datetime.now(UTC),
        type="command",
        data={"line": line, "reply": ""},
    )


def _scripted_events() -> list[SessionEvent]:
    """Run the scripted attacker and return its events as contract types."""
    raw = SshLikeShell("192.0.2.50").run(SCRIPTED_ATTACKER)
    return [SessionEvent(**e) for e in raw]


class TestMitreTable:
    def test_every_row_has_all_required_fields(self):
        required = {
            "technique_id",
            "name",
            "keyword",
            "evidence_template",
            "source_url",
            "verified_date",
        }
        for row in MITRE_TABLE:
            missing = required - set(vars(row).keys())
            assert not missing, f"{row.technique_id} is missing fields: {missing}"

    def test_all_required_technique_ids_present(self):
        expected_ids = {
            "T1071.004",
            "T1572",
            "T1048",
            "T1059.004",
            "T1082",
            "T1083",
            "T1033",
            "T1105",
        }
        actual_ids = {row.technique_id for row in MITRE_TABLE}
        assert expected_ids == actual_ids

    def test_row_without_verified_date_is_unverified(self):
        unverified_rows = [row for row in MITRE_TABLE if row.verified_date is None]
        assert len(unverified_rows) == len(MITRE_TABLE), "all rows should be Unverified initially"

        for row in unverified_rows:
            events = [_make_event(row.keyword)]
            tags = tag_events(events)
            matching = [t for t in tags if t.technique_id == row.technique_id]
            assert matching, f"no tag produced for keyword '{row.keyword}'"
            assert UNVERIFIED in matching[0].evidence, (
                f"expected '{UNVERIFIED}' in evidence for {row.technique_id}"
            )

    def test_verified_date_appears_in_evidence_when_set(self):
        row = MitreRow(
            technique_id="T9999",
            name="Test Technique",
            keyword="test_cmd",
            evidence_template="matched '{keyword}'",
            source_url="https://attack.mitre.org/techniques/T9999/",
            verified_date="2026-10-21",
        )
        label = _verification_label(row)
        assert label == "2026-10-21"


class TestTagEvents:
    def test_scripted_attacker_produces_expected_tags(self):
        events = _scripted_events()
        tags = tag_events(events)

        # T1059.004 is absent on purpose: its keyword '/bin/sh' only appears in a
        # reply, and tagging reads the typed command line only.
        assert [(t.technique_id, t.name, t.evidence) for t in tags] == [
            (
                "T1033",
                "System Owner/User Discovery",
                "command matched user-discovery keyword 'whoami' [Unverified]",
            ),
            (
                "T1082",
                "System Information Discovery",
                "command matched system-info keyword 'uname' [Unverified]",
            ),
            (
                "T1083",
                "File and Directory Discovery",
                "command matched file-discovery keyword 'cat /etc/passwd' [Unverified]",
            ),
            (
                "T1071.004",
                "Application Layer Protocol: DNS",
                "command matched DNS-tunnel keyword 'iodine' [Unverified]",
            ),
            (
                "T1572",
                "Protocol Tunneling",
                "command matched tunneling keyword 'iodine -f' [Unverified]",
            ),
            (
                "T1048",
                "Exfiltration Over Alternative Protocol",
                "command matched exfiltration-channel keyword 'iodine' [Unverified]",
            ),
        ]

    def test_scripted_attacker_tags_have_evidence_lines(self):
        events = _scripted_events()
        tags = tag_events(events)
        for tag in tags:
            assert tag.evidence, f"{tag.technique_id} has empty evidence"

    def test_unknown_command_gives_no_tag(self):
        events = [_make_event("zork --play-game")]
        tags = tag_events(events)
        assert tags == [], f"unexpected tags for unknown command: {tags}"

    def test_empty_events_gives_no_tag(self):
        tags = tag_events([])
        assert tags == []

    def test_non_command_event_gives_no_tag(self):
        event = SessionEvent(
            ts=datetime.now(UTC),
            type="connect",
            data={"attacker_addr": "192.0.2.50", "banner": "SSH-like service"},
        )
        tags = tag_events([event])
        assert tags == []

    def test_each_technique_appears_at_most_once(self):
        events = [_make_event("whoami"), _make_event("whoami")]
        tags = tag_events(events)
        ids = [t.technique_id for t in tags]
        assert len(ids) == len(set(ids)), "duplicate technique ids in output"

    def test_tags_are_mitre_tag_contracts(self):
        events = [_make_event("whoami")]
        tags = tag_events(events)
        for tag in tags:
            assert isinstance(tag, MitreTag)
