"""Fetch a public flow dataset into data/<name>/ (gitignored).

Usage: python scripts/FetchData.py cic-ids2017-csv [--allow-large]

Refuses any download over 1 GB unless --allow-large is given.
Sources are listed in data/README.md; confirm the URL there before first use.
"""

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

LIMIT_BYTES = 1_000_000_000
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

SOURCES = {
    "cic-ids2017-csv": (
        "http://cicresearch.ca/CICDataset/CIC-IDS-2017/Dataset/CIC-IDS-2017/CSVs/MachineLearningCSV.zip",
        "cic-ids2017",
    ),
}


def check_size(size: int | None, allow_large: bool) -> None:
    if size is None:
        raise SystemExit("server gave no Content-Length; refusing blind download")
    if size > LIMIT_BYTES and not allow_large:
        raise SystemExit(f"{size / 1e9:.1f} GB is over 1 GB; ask Ayush, then pass --allow-large")


def remote_size(url: str) -> int | None:
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=30) as resp:
        length = resp.headers.get("Content-Length")
    return int(length) if length else None


def fetch(name: str, allow_large: bool) -> Path:
    url, folder = SOURCES[name]
    check_size(remote_size(url), allow_large)
    dest = DATA_DIR / folder
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / url.rsplit("/", 1)[1]
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=60) as resp, out.open("wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
            digest.update(chunk)
    print(f"saved {out}\nsha256 {digest.hexdigest()}\nrecord both in data/README.md")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("name", choices=sorted(SOURCES))
    parser.add_argument("--allow-large", action="store_true")
    args = parser.parse_args(argv)
    fetch(args.name, args.allow_large)
    return 0


if __name__ == "__main__":
    sys.exit(main())
