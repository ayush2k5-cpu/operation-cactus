from collections.abc import Iterator
from typing import Protocol

from contracts.models import FlowRecord


class CaptureSource(Protocol):
    """Anything that turns packets into FlowRecords (replay today, a live sensor later)."""

    def flows(self) -> Iterator[FlowRecord]: ...
