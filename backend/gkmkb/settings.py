"""Gate settings from the environment (.env), with safe defaults when unset."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gate_window_seconds: float = 60.0
    gate_threshold: float = 0.7


def load_settings() -> Settings:
    defaults = Settings()
    return Settings(
        gate_window_seconds=float(
            os.environ.get("GATE_WINDOW_SECONDS") or defaults.gate_window_seconds
        ),
        gate_threshold=float(os.environ.get("GATE_THRESHOLD") or defaults.gate_threshold),
    )
