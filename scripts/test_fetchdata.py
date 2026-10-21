import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
import FetchData  # noqa: E402


def test_small_download_allowed() -> None:
    FetchData.check_size(224_000_000, allow_large=False)


def test_large_download_refused_without_flag() -> None:
    with pytest.raises(SystemExit):
        FetchData.check_size(48_000_000_000, allow_large=False)


def test_large_download_allowed_with_flag() -> None:
    FetchData.check_size(48_000_000_000, allow_large=True)


def test_unknown_size_refused() -> None:
    with pytest.raises(SystemExit):
        FetchData.check_size(None, allow_large=True)


def test_download_target_is_gitignored_data_dir() -> None:
    assert FetchData.DATA_DIR.name == "data"
