"""Simple lookup table for Etrel connector status codes."""

CONNECTOR_STATUS: dict[int, str] = {
    0: "Unknown",
    1: "SocketAvailable",
    2: "WaitingForVehicleToBeConnected",
    3: "WaitingForVehicleToStart",
    4: "Charging",
    5: "ChargingPausedByEv",
    6: "ChargingPausedByEvse",
    7: "ChargingEnded",
    8: "ChargingFault",
    9: "UnpausingCharging",
    10: "Unavailable",
}

def get_connector_status(code: int) -> str:
    """Return the human-readable status for a connector code."""
    return CONNECTOR_STATUS.get(code, f"Unknown({code})")

CONNECTOR_TYPE: dict[int, str] = {
    1: "SocketType",
    2: "PlugType",
}

def get_connector_type(code: int) -> str:
    """Return the human-readable connector type for a code."""
    return CONNECTOR_TYPE.get(code, f"Unknown({code})")

MEASURED_PHASES: dict[int, str] = {
    0: "Three phases",
    1: "Single phase L1",
    2: "Single phase L2",
    3: "Single phase L3",
    4: "Unknown",
    5: "Two phases",
}

def get_measured_phases(code: int) -> str:
    """Return the human-readable measured phases for a code."""
    return MEASURED_PHASES.get(code, f"Unknown({code})")