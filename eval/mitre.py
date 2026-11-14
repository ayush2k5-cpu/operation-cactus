"""MITRE ATT&CK keyword table and session-event tagging for GKMKB eval.

Technique IDs and canonical names are verified against attack.mitre.org. Unknown
commands produce no tag. Imports only from contracts/.
"""

from dataclasses import dataclass

from contracts.models import MitreTag, SessionEvent

UNVERIFIED = "Unverified"


@dataclass(frozen=True)
class MitreRow:
    technique_id: str
    name: str
    keyword: str
    evidence_template: str
    source_url: str
    verified_date: str | None


MITRE_TABLE: list[MitreRow] = [
    MitreRow(
        technique_id="T1071.004",
        name="Application Layer Protocol: DNS",
        keyword="iodine",
        evidence_template="command matched DNS-tunnel keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1071/004/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1572",
        name="Protocol Tunneling",
        keyword="iodine -f",
        evidence_template="command matched tunneling keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1572/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1048",
        name="Exfiltration Over Alternative Protocol",
        keyword="iodine",
        evidence_template="command matched exfiltration-channel keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1048/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1059.004",
        name="Command and Scripting Interpreter: Unix Shell",
        keyword="/bin/sh",
        evidence_template="command matched shell-interpreter keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1059/004/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1082",
        name="System Information Discovery",
        keyword="uname",
        evidence_template="command matched system-info keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1082/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1083",
        name="File and Directory Discovery",
        keyword="cat /etc/passwd",
        evidence_template="command matched file-discovery keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1083/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1033",
        name="System Owner/User Discovery",
        keyword="whoami",
        evidence_template="command matched user-discovery keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1033/",
        verified_date="2026-11-14",
    ),
    MitreRow(
        technique_id="T1105",
        name="Ingress Tool Transfer",
        keyword="wget",
        evidence_template="command matched tool-transfer keyword '{keyword}'",
        source_url="https://attack.mitre.org/techniques/T1105/",
        verified_date="2026-11-14",
    ),
]


def _verification_label(row: MitreRow) -> str:
    return row.verified_date if row.verified_date is not None else UNVERIFIED


def tag_events(events: list[SessionEvent]) -> list[MitreTag]:
    """Return MITRE tags for session events. Unknown commands produce no tag.

    Each tag carries an evidence line. A row without verified_date is labelled
    Unverified. Each technique appears at most once per call.
    """
    seen: set[str] = set()
    tags: list[MitreTag] = []

    for event in events:
        if event.type != "command":
            continue
        line: str = event.data.get("line", "")
        for row in MITRE_TABLE:
            if row.technique_id in seen:
                continue
            if row.keyword in line:
                evidence = (
                    row.evidence_template.format(keyword=row.keyword)
                    + f" [{_verification_label(row)}]"
                )
                tags.append(
                    MitreTag(
                        technique_id=row.technique_id,
                        name=row.name,
                        evidence=evidence,
                    )
                )
                seen.add(row.technique_id)

    return tags
