import json
from pathlib import Path
from dataclasses import dataclass
from typing import Dict

@dataclass(frozen=True)
class StatusSnapshot:
    """
    Immutable snapshot of endpoint online status at a given timestamp.

    Attributes:
        ts: Unix timestamp of the snapshot.
        online_by_id: Mapping from endpoint ID to online status (True/False).
    """
    ts: int
    online_by_id: Dict[str, bool]

def load_status_snapshot(path: str) -> StatusSnapshot:
    """
    Load a StatusSnapshot from a JSON file.

    Args:
        path: Path to the JSON file containing the status snapshot.

    Returns:
        StatusSnapshot instance with timestamp and online status mapping.
    """
    data = json.loads(Path(path).read_text())
    ts = int(data.get("ts", 0))
    online_by_id: Dict[str, bool] = {}
    for k, v in data.items():
        if k == "ts":
            continue
        online_by_id[str(k)] = bool(v.get("online", False))
    return StatusSnapshot(ts=ts, online_by_id=online_by_id)