#!/usr/bin/env python3
"""
Etrel INCH (Duo) Modbus TCP write tool (PyModbus 3.x compatible)

- Replaces old pymodbus.payload.BinaryPayloadBuilder + skip_encode=True
- Uses struct packing to 16-bit registers (big-endian words)
- Handles varying unit kwarg names across pymodbus versions: slave/unit/device_id

Vendor original: Version 2.6, Nov 2022 (Samir Gutić, ETREL doo)
Modernized for PyModbus 3.x
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from struct import pack, unpack
from typing import Iterable

from pymodbus.client import ModbusTcpClient


# ----------------------------
# Config
# ----------------------------

UNIT = 1
SEPARATOR = 65

CLIENT_PORT = 502
CLIENT_PORT_CLUSTER = 503

# PLEASE CHANGE CHARGER'S IP ADDRESS FIRST
CLIENT_IP = "192.168.1.121"


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


def regs_i64_be(v: int) -> list[int]:
    """Int64 -> 4 registers (ABCD EFGH)"""
    return _regs_from_bytes_be(pack(">q", int(v)))


def regs_rfid_byte_per_reg(hexstr: str, n_regs: int = 10) -> list[int]:
    """
    Vendor script behavior: take hex string like '06CD962A'
    and store each *byte* into one register (0..255), padded to n_regs.
    """
    hexstr = hexstr.strip().replace(" ", "")
    if len(hexstr) % 2:
        raise ValueError("RFID hex string must have even length (pairs of hex digits).")
    b = bytes.fromhex(hexstr)
    regs = [x for x in b[:n_regs]]
    regs.extend([0] * (n_regs - len(regs)))
    return regs


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
# Menu data
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


# ----------------------------
# UI helpers
# ----------------------------

def hr():
    print("-" * SEPARATOR)


def print_main_menu(ip: str, connector: str):
    hr()
    print(f"AVAILABLE WRITING OPTIONS for {ip} (connector {connector})")
    hr()
    print(">>> CONNECTOR COMMANDS <<<")
    print(" 1. Stop charging")
    print(" 2. Pause charging")
    print(" 3. Set departure time")
    print(" 4. Set current setpoint")
    print(" 5. Cancel current setpoint")
    print(" 6. Set power setpoint")
    print(" 7. Cancel power setpoint")
    print(" 8. Send RFID tag")
    print("\n>>> CHARGER COMMANDS <<<")
    print(" 9. Set time")
    print("10. Restart charger")
    print("\n>>> CLUSTER COMMANDS <<<")
    print("11. Cluster - set limit L1")
    print("12. Cluster - set limit L2")
    print("13. Cluster - set limit L3")
    hr()


def safe_int(prompt: str) -> int:
    return int(input(prompt).strip())


def safe_float(prompt: str) -> float:
    return float(input(prompt).strip())


# ----------------------------
# Actions
# ----------------------------

def do_connector_actions(client: ModbusTcpClient, cm: ConnectorMap, option: str):
    if option == "1":
        write_single_trigger(client, address=cm.stop, unit_id=UNIT)
        print(f"[{cm.stop}] Stop charging")

    elif option == "2":
        write_single_trigger(client, address=cm.pause, unit_id=UNIT)
        print(f"[{cm.pause}] Pause charging")

    elif option == "3":
        unix_time = safe_int("Please enter UNIX timestamp: ")
        regs = regs_i64_be(unix_time)
        write_registers_compat(client, address=cm.departure_time, values=regs, unit_id=UNIT)
        print(f"[{cm.departure_time}] Set departure time to: {datetime.utcfromtimestamp(unix_time).strftime('%H:%M:%S %d-%m-%Y')} UTC")

    elif option == "4":
        amps = safe_float("Please enter current setpoint in A (e.g. 6.6): ")
        if not (6.0 <= amps <= 32.0):
            print(f"Unsupported value ({amps}). Value must be between 6.0 and 32.0")
            return
        regs = regs_f32_be(amps)
        write_registers_compat(client, address=cm.current_setpoint, values=regs, unit_id=UNIT)
        print(f"[{cm.current_setpoint}] Set current setpoint to: {int(amps)}A (charger targets integer)")

    elif option == "5":
        write_single_trigger(client, address=cm.cancel_current_setpoint, unit_id=UNIT)
        print(f"[{cm.cancel_current_setpoint}] Cancel current setpoint")

    elif option == "6":
        kw = safe_float("Please enter power setpoint in kW (e.g. 11.1): ")
        if kw > 22.0:
            print(f"Unsupported value ({kw}). Value must be <= 22.0")
            return
        regs = regs_f32_be(kw)
        write_registers_compat(client, address=cm.power_setpoint, values=regs, unit_id=UNIT)
        print(f"[{cm.power_setpoint}] Set power setpoint to: {kw} kW")

    elif option == "7":
        write_single_trigger(client, address=cm.cancel_power_setpoint, unit_id=UNIT)
        print(f"[{cm.cancel_power_setpoint}] Cancel power setpoint")

    elif option == "8":
        tag = input("Please enter RFID tag (e.g. 06CD962A): ").strip()
        regs = regs_rfid_byte_per_reg(tag, n_regs=10)
        write_registers_compat(client, address=cm.rfid, values=regs, unit_id=UNIT)
        print(f"[{cm.rfid}] Send RFID tag {tag}")

    else:
        raise ValueError("Internal: invalid connector option")


def do_charger_actions(client: ModbusTcpClient, option: str):
    if option == "9":
        unix_time = safe_int("Please enter UNIX timestamp: ")
        regs = regs_i64_be(unix_time)
        write_registers_compat(client, address=CHARGER_SET_TIME, values=regs, unit_id=UNIT)
        print(f"[{CHARGER_SET_TIME}] Set time to: {datetime.utcfromtimestamp(unix_time).strftime('%H:%M:%S %d-%m-%Y')} UTC")

    elif option == "10":
        write_single_trigger(client, address=CHARGER_RESTART, unit_id=UNIT)
        print(f"[{CHARGER_RESTART}] Restart charger")

    else:
        raise ValueError("Internal: invalid charger option")


def do_cluster_actions(ip: str, option: str):
    # Cluster uses port 503
    client = ModbusTcpClient(ip, port=CLIENT_PORT_CLUSTER)
    if not client.connect():
        print(f"Could not connect to {ip}:{CLIENT_PORT_CLUSTER}")
        return
    try:
        if option == "11":
            addr = CLUSTER_L1
            phase = "L1"
        elif option == "12":
            addr = CLUSTER_L2
            phase = "L2"
        elif option == "13":
            addr = CLUSTER_L3
            phase = "L3"
        else:
            raise ValueError("Internal: invalid cluster option")

        amps = safe_float(f"Please enter cluster current limit for {phase} in A (e.g. 6.6): ")
        if amps < 6.0:
            print(f"Unsupported value ({amps}). Value must be >= 6.0")
            return

        regs = regs_f32_be(amps)
        write_registers_compat(client, address=addr, values=regs, unit_id=UNIT)
        print(f"[{addr}] Cluster - set limit {phase} to: {amps} A")

    finally:
        client.close()


# ----------------------------
# Main loop
# ----------------------------

def main():
    connector = "a"

    # Main client for port 502 (charger)
    client = ModbusTcpClient(CLIENT_IP, port=CLIENT_PORT)
    if not client.connect():
        print(f"Could not connect to {CLIENT_IP}:{CLIENT_PORT}")
        return

    try:
        while connector != "e":
            hr()
            connector = input(f"Please enter connector number 1 or 2 for {CLIENT_IP} (e to exit): ").strip()

            if connector == "e":
                break
            if connector not in ("1", "2"):
                print(f"Connector number {connector} doesn't exist. Please enter 1 or 2.")
                continue

            cm = CONNECTOR_1 if connector == "1" else CONNECTOR_2

            option = "a"
            while option != "e":
                try:
                    print_main_menu(CLIENT_IP, connector)
                    option = input("Please enter option number (1 to 13 or e to exit): ").strip()

                    if option == "e":
                        break

                    # connector writes and charger writes use port 502 client
                    if option in ("1", "2", "3", "4", "5", "6", "7", "8"):
                        hr()
                        print("Connection:", client)
                        do_connector_actions(client, cm, option)

                    elif option in ("9", "10"):
                        hr()
                        print("Connection:", client)
                        do_charger_actions(client, option)

                    elif option in ("11", "12", "13"):
                        do_cluster_actions(CLIENT_IP, option)

                    else:
                        print("*" * SEPARATOR)
                        print(f"You have entered unsupported option ({option})")
                        print("*" * SEPARATOR)

                except Exception as e:
                    hr()
                    print(f"An error has occurred during writing: {e!r}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
