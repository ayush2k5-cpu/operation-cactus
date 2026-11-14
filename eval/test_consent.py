"""Tests for the team capture consent record (ticket #83).

Acceptance criteria:
- One consent line per teammate: name, date, what may be captured
- One line per benign capture: who, date, consent given (no machine names, hostnames or IPs: public repo)
- The report outline consent placeholder points to this record
- Captures were checked for personal data before commit
"""

import re
from pathlib import Path

CONSENT_RECORD_PATH = Path("docs/report/ConsentRecord.md")
TEAM_MEMBERS = [
    "Ayush Rathod",
    "Sharukh Khan",
    "Shivansh Tripathi",
    "Bhargav Moray",
]


def test_consent_record_exists_and_non_empty():
    assert CONSENT_RECORD_PATH.exists(), f"Missing consent record at {CONSENT_RECORD_PATH}"
    content = CONSENT_RECORD_PATH.read_text(encoding="utf-8").strip()
    assert len(content) > 100, "Consent record is unexpectedly short"


def test_every_teammate_has_consent_line():
    content = CONSENT_RECORD_PATH.read_text(encoding="utf-8")
    for name in TEAM_MEMBERS:
        pattern = (
            rf"I,\s+{re.escape(name)},\s+agree that DNS and network traffic generated on my own machine,"
            rf"\s+for this project's lab tests only,\s+may be captured,\s+stored in the project's data folder"
            rf"\s+after a check for personal data,\s+and published as part of the project's public repository\."
            rf"\s+I can withdraw this for future captures at any time\.\s+Date:\s+\d{{4}}-\d{{2}}-\d{{2}}\."
        )
        match = re.search(pattern, content)
        assert match is not None, f"Missing or invalid consent line for {name}"


def test_consent_record_contains_no_ip_addresses():
    """Privacy check: Public repository record must not leak IP addresses."""
    content = CONSENT_RECORD_PATH.read_text(encoding="utf-8")
    # Matches common IPv4 addresses
    ipv4_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
    matches = re.findall(ipv4_pattern, content)
    assert matches == [], f"Found IP address leaked in consent record: {matches}"


def test_benign_captures_log_section_present():
    content = CONSENT_RECORD_PATH.read_text(encoding="utf-8")
    assert "## Benign Captures Log" in content
    assert "Personal data check done" in content
