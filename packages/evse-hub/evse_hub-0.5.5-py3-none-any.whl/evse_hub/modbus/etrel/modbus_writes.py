from __future__ import annotations

from struct import pack, unpack
from pymodbus.client import ModbusTcpClient
from dataclasses import dataclass
from typing import Any, Iterable


# ----------------------------
# Packing helpers (BE word order, BE byte order inside each register)
# ----------------------------

def _regs_from_bytes_be(b: bytes) -> list[int]:
    """Split bytes into big-endian 16-bit registers."""
    if len(b) % 2:
        raise ValueError("Byte length must be even to convert to 16-bit registers.")
    return [unpack(">H", b[i:i+2])[0] for i in range(0, len(b), 2)]

def regs_f32_be(v: float) -> list[int]:
    """Float32 -> 2 registers (ABCD)"""
    return _regs_from_bytes_be(pack(">f", float(v)))


# ----------------------------
# PyModbus kwarg compatibility shim
# ----------------------------

def write_registers_compat(
    client: ModbusTcpClient,
    *,
    address: int,
    values: Iterable[int],
    unit_id: int,
):
    """
    pymodbus kwarg name varies by version: slave / unit / device_id / none.
    Try the common ones.
    """
    fn = client.write_registers
    vals = [int(v) & 0xFFFF for v in values]

    for kw in ("slave", "unit", "device_id"):
        try:
            return fn(address=address, values=vals, **{kw: unit_id})
        except TypeError:
            pass

    # Fallback: no unit parameter
    return fn(address=address, values=vals)


def write_single_trigger(
    client: ModbusTcpClient,
    *,
    address: int,
    unit_id: int,
):
    """
    For 'value ignored, triggered by write' commands, vendor uses FC16 anyway.
    We'll write one register with value 1.
    """
    return write_registers_compat(client, address=address, values=[1], unit_id=unit_id)

# ----------------------------
# Address maps
# ----------------------------

@dataclass(frozen=True)
class ConnectorMap:
    stop: int
    pause: int
    departure_time: int
    current_setpoint: int
    cancel_current_setpoint: int
    power_setpoint: int
    cancel_power_setpoint: int
    rfid: int


CONNECTOR_1 = ConnectorMap(
    stop=1,
    pause=2,
    departure_time=4,
    current_setpoint=8,
    cancel_current_setpoint=10,
    power_setpoint=11,
    cancel_power_setpoint=13,
    rfid=14,
)

CONNECTOR_2 = ConnectorMap(
    stop=101,
    pause=102,
    departure_time=104,
    current_setpoint=108,
    cancel_current_setpoint=110,
    power_setpoint=111,
    cancel_power_setpoint=113,
    rfid=114,
)

CHARGER_SET_TIME = 1000
CHARGER_RESTART = 1004

CLUSTER_L1 = 2000
CLUSTER_L2 = 2002
CLUSTER_L3 = 2004


def set_current_setpoint(client: ModbusTcpClient, unit: int, *, amps: float, connector: int = 1) -> dict[str, Any]:
    """
    Set the current setpoint for an EV charger connector via Modbus.
    
    Args:
        client: Modbus TCP client connection.
        unit: Modbus unit ID (device address).
        amps: Charging current setpoint in Amperes. Must be between 6.0 and 16.0.
        connector: Connector number (1 or 2, default 1).
    
    Raises:
        ValueError: If amps is not convertible to float or outside the range [6.0, 16.0].
    """
    cm = CONNECTOR_1 if connector == 1 else CONNECTOR_2
    # Validate amps is a float and within range [6, 16]
    try:
        amps = float(amps)
    except (TypeError, ValueError):
        raise ValueError(f"amps must be convertible to float, got {type(amps).__name__}")
    if not (6.0 <= amps <= 16.0):
        raise ValueError(f"amps must be between 6.0 and 16.0, got {amps}")
    
    regs = regs_f32_be(amps)
    resp = write_registers_compat(client, address=cm.current_setpoint, values=regs, unit_id=unit)

    ok = True
    if hasattr(resp, "isError"):
        ok = not resp.isError()

    return {"ok": ok, "amps_set": amps, "connector": connector}
    

def cancel_current_setpoint(client: ModbusTcpClient, unit: int, *, connector: int = 1) -> dict[str, Any]:
    """
    Cancel the current setpoint for an EV charger connector via Modbus.
    
    Clears any previously set current setpoint, allowing the charger to determine
    its own charging current limits.
    
    Args:
        client: Modbus TCP client connection.
        unit: Modbus unit ID (device address).
        connector: Connector number (1 or 2, default 1).
    """

    cm = CONNECTOR_1 if connector == 1 else CONNECTOR_2
    
    resp = write_single_trigger(client, address=cm.cancel_current_setpoint, unit_id=unit)

    ok = True
    if hasattr(resp, "isError"):
        ok = not resp.isError()

    return {"ok": ok, "current_setpoint_canceled": True, "connector": connector}