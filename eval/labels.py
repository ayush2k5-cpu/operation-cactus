"""Labels file parsing and resolution for GKMKB evaluation.

A labels file sits beside each pcap, naming each Entity (src_ip, dst_ip) as 'tunnel' or 'benign'.
Ground truth is written by the person who made the capture, never derived from detector output.
"""

from pathlib import Path


def load_labels(path: Path | str) -> dict[tuple[str, str], str]:
    """Load Entity labels from a labels file.

    Format: one row per Entity:
        src_ip,dst_ip,label
    where label is either 'tunnel' or 'benign'. Lines starting with '#' or empty lines
    are ignored. An optional header row ('src_ip,...') is skipped.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Missing labels file: {path}")

    labels: dict[tuple[str, str], str] = {}
    content = path.read_text(encoding="utf-8")
    for line_num, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        # Support comma-separated or whitespace-separated
        parts = [p.strip() for p in (line.split(",") if "," in line else line.split())]
        if len(parts) != 3:
            raise ValueError(
                f"Invalid row at line {line_num} in {path}: expected 3 columns (src_ip, dst_ip, label), got {len(parts)}"
            )
        src, dst, label = parts[0], parts[1], parts[2].lower()
        if src.lower() in ("src_ip", "src", "source") and label in ("label", "kind", "type"):
            # Header line
            continue
        if label not in ("tunnel", "benign"):
            raise ValueError(
                f"Invalid label '{label}' at line {line_num} in {path}: must be 'tunnel' or 'benign'"
            )
        labels[(src, dst)] = label

    return labels


def find_labels_file(pcap_path: Path | str) -> Path:
    """Find the labels file corresponding to a pcap file.

    Checks standard naming conventions beside the pcap. Raises FileNotFoundError
    with a clear message if no labels file exists.
    """
    pcap = Path(pcap_path)
    candidates = [
        pcap.with_suffix(".labels"),
        pcap.with_suffix(".labels.csv"),
        pcap.parent / f"{pcap.name}.labels",
        pcap.with_suffix(".labels.txt"),
    ]
    for cand in candidates:
        if cand.is_file():
            return cand

    expected = pcap.with_suffix(".labels")
    raise FileNotFoundError(
        f"Missing labels file for pcap '{pcap}': expected labels file at '{expected}'"
    )
