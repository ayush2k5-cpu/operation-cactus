"""Settings from the environment (.env), with safe defaults when unset."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    gate_window_seconds: float = 60.0
    gate_threshold: float = 0.7
    replay_event_delay_ms: float = 0.0
    data_dir: str = "data"
    mongo_uri: str = ""
    mongo_db: str = "gkmkb"
    api_host: str = "127.0.0.1"


def load_settings() -> Settings:
    defaults = Settings()
    return Settings(
        gate_window_seconds=float(
            os.environ.get("GATE_WINDOW_SECONDS") or defaults.gate_window_seconds
        ),
        gate_threshold=float(os.environ.get("GATE_THRESHOLD") or defaults.gate_threshold),
        replay_event_delay_ms=float(
            os.environ.get("REPLAY_EVENT_DELAY_MS") or defaults.replay_event_delay_ms
        ),
        data_dir=os.environ.get("DATA_DIR") or defaults.data_dir,
        mongo_uri=os.environ.get("MONGO_URI") or defaults.mongo_uri,
        mongo_db=os.environ.get("MONGO_DB") or defaults.mongo_db,
        api_host=os.environ.get("API_HOST") or defaults.api_host,
    )
