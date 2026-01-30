from __future__ import annotations

from struct import pack, unpack
from pymodbus.client import ModbusTcpClient
from typing import Any
from .etrel import *


def _f32_be(regs: list[int], idx: int) -> float:
    """Convert big-endian 32-bit float from register list.
    
    Args:
        regs: List of register values.
        idx: Starting index in the register list.
    
    Returns:
        The decoded float value.
    """
    raw = pack(">HH", int(regs[idx]) & 0xFFFF, int(regs[idx + 1]) & 0xFFFF)
    return float(unpack(">f", raw)[0])


def _i64_be(regs: list[int], idx: int) -> int:
    """Convert big-endian 64-bit signed integer from register list.
    
    Args:
        regs: List of register values.
        idx: Starting index in the register list.
    
    Returns:
        The decoded 64-bit signed integer value.
    """
    raw = pack(
        ">HHHH",
        int(regs[idx]) & 0xFFFF,
        int(regs[idx + 1]) & 0xFFFF,
        int(regs[idx + 2]) & 0xFFFF,
        int(regs[idx + 3]) & 0xFFFF,
    )
    return int(unpack(">q", raw)[0])

def _u32_be(regs: list[int], idx: int) -> int:
    """Convert big-endian 32-bit signed integer from register list.
    
    Args:
        regs: List of register values.
        idx: Starting index in the register list.
    
    Returns:
        The decoded 32-bit signed integer value.
    """
    raw = pack(">HH", int(regs[idx + 1]) & 0xFFFF, int(regs[idx]) & 0xFFFF)
    return int(unpack(">i", raw)[0])


def _ascii_be(regs: list[int], idx: int, n_regs: int, *, strip_null: bool = True) -> str:
    """Decode ASCII string from big-endian register list.
    
    Args:
        regs: List of register values.
        idx: Starting index in the register list.
        n_regs: Number of registers to decode.
        strip_null: If True, stop at first null character. Defaults to True.
    
    Returns:
        The decoded ASCII string with trailing whitespace removed.
    """
    b = bytearray()
    for r in regs[idx: idx + n_regs]:
        r &= 0xFFFF
        b.append((r >> 8) & 0xFF)   # high byte
        b.append(r & 0xFF)          # low byte

    if strip_null:
        b = b.split(b"\x00", 1)[0]  # stop at first NUL

    return b.decode("ascii", errors="replace").rstrip()

def _read_input_registers(client: ModbusTcpClient, *, address: int, count: int, unit_id: int):
    """Read input registers from Modbus device with version-agnostic kwarg handling.
    
    The pymodbus library uses different kwarg names (slave/unit/device_id) across versions.
    This function attempts to handle these variations gracefully.
    
    Args:
        client: The ModbusTcpClient instance.
        address: Starting register address.
        count: Number of registers to read.
        unit_id: The device unit ID.
    
    Returns:
        The response object containing the register values.
    """
    fn = client.read_input_registers

    # Try keyword variations first
    for kw in ("slave", "unit", "device_id"):
        try:
            return fn(address=address, count=count, **{kw: unit_id})
        except TypeError:
            pass

    # Fallback: no unit parameter (some setups default to unit 1)
    return fn(address=address, count=count)

def read_master_loadguard(client: ModbusTcpClient, unit: int) -> dict[str, Any]:
    """Read master loadguard status and electrical measurements.
    
    Retrieves connection status and three-phase voltage, current, and total power
    measurements from the master loadguard device.
    
    Args:
        client: The ModbusTcpClient instance.
        unit: The device unit ID.
    
    Returns:
        Dictionary containing loadguard status and electrical measurements:
            - lg_connected: Connection status (bool or None)
            - lg_status: Status description (str)
            - u_l1_V: Phase 1 voltage in volts
            - u_l2_V: Phase 2 voltage in volts
            - u_l3_V: Phase 3 voltage in volts
            - i_l1_A: Phase 1 current in amperes
            - i_l2_A: Phase 2 current in amperes
            - i_l3_A: Phase 3 current in amperes
            - p_total_kW: Total power in kilowatts
    
    Raises:
        RuntimeError: If the register read fails.
    """
    rr = _read_input_registers(client, address=2000, count=26, unit_id=unit)
    if rr.isError():
        raise RuntimeError(rr)

    r = rr.registers

    lg_raw = int(r[0])
    if lg_raw == 0:
        lg_status = "Not connected"
        lg_connected = False
    elif lg_raw == 1:
        lg_status = "Connected"
        lg_connected = True
    else:
        lg_status = "Unknown connection status!"
        lg_connected = None

    u_l1 = _f32_be(r, 2004 - 2000)
    u_l2 = _f32_be(r, 2006 - 2000)
    u_l3 = _f32_be(r, 2008 - 2000)

    i_l1 = _f32_be(r, 2010 - 2000)
    i_l2 = _f32_be(r, 2012 - 2000)
    i_l3 = _f32_be(r, 2014 - 2000)

    p_tot = _f32_be(r, 2022 - 2000)

    return {
        "lg_connected": lg_connected,
        "lg_status": lg_status,
        "u_l1_V": round(u_l1, 2),
        "u_l2_V": round(u_l2, 2),
        "u_l3_V": round(u_l3, 2),
        "i_l1_A": round(i_l1, 2),
        "i_l2_A": round(i_l2, 2),
        "i_l3_A": round(i_l3, 2),
        "p_total_kW": round(p_tot, 2),
    }


def read_evse(client: ModbusTcpClient, unit: int) -> dict[str, Any]:
    """Read EVSE (electric vehicle supply equipment) connector status and power.
    
    Args:
        client: The ModbusTcpClient instance.
        unit: The device unit ID.
    
    Returns:
        Dictionary containing EVSE status:
            - connector_status: Current connector status (str)
            - power_kW: Current power output in kilowatts
    
    Raises:
        RuntimeError: If a register read fails.
    """

    rr = _read_input_registers(client, address=0, count=1, unit_id=unit)
    if rr.isError():
        raise RuntimeError(rr)
    r = rr.registers
    connector_status = int(r[0])

    rr = _read_input_registers(client, address=26, count=2, unit_id=unit)
    if rr.isError():
        raise RuntimeError(rr)
    r = rr.registers
    power_kW = _f32_be(r, 0)
    return {
        "connector_status": connector_status,
        "power_kW": round(power_kW, 2),
    }


