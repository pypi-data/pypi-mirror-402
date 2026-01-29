from evse_hub.modbus.modbus_device import ModbusDevice
from evse_hub.modbus.etrel.modbus_reads import _read_input_registers, _f32_be, _ascii_be, _i64_be, _u32_be
from evse_hub.tools.config import load_secrets
from evse_hub.modbus.etrel.etrel import *

evses=load_secrets("evse.yml")['devices']

for evse in evses:
    try:
        
        dev=ModbusDevice(evse["name"], evse["ip"], 502, timeout_s=2.0)
        client = dev.ensure_client()
        ok=client.connect()
        print(f"\n{evse["name"]} connected: {ok}\n")
        rr=_read_input_registers(client, address=0, count=48, unit_id=1)
        r=rr.registers
        print(f"Connector status: {CONNECTOR_STATUS[r[0]]}")
        print(f"Connector measured number of phases: {MEASURED_PHASES[r[1]]}")
        print(f"EV max phase current: {_f32_be(r, 2)} A")
        print(f"Target current from power mgm or modbus: {_f32_be(r, 4)} A")
        print(f"Frequency: {_f32_be(r, 6):.3f} Hz")
        print(f"L1-N Voltage: {_f32_be(r, 8):.1f} V")

        print(f"L2-N Voltage: {_f32_be(r, 10):.1f} V")
        print(f"L3-N Voltage: {_f32_be(r, 12):.1f} V")
        print(f"L1 Current: {_f32_be(r, 14):.2f} A")
        print(f"L2 Current: {_f32_be(r, 16):.2f} A")
        print(f"L3 Current: {_f32_be(r, 18):.2f} A")
        print(f"Active power L1: {_f32_be(r, 20):.2f} kW")
        print(f"Active power L2: {_f32_be(r, 22):.2f} kW")
        print(f"Active power L3: {_f32_be(r, 24):.2f} kW")
        print(f"Total power: {_f32_be(r, 26):.2f} kW")
        print(f"Total imported active energy in running session: {_f32_be(r, 30):.2f} kWh")
        print(f"Running session max power: {_f32_be(r, 44):.2f} kW")

        rr=_read_input_registers(client, address=990, count=40, unit_id=1)
        r=rr.registers
        print(f"Serial number: {(_ascii_be(r, 0, 10))}")
        print(f"Model: {(_ascii_be(r, 1000-990, 10))}")
        print(f"HW Version: {(_ascii_be(r, 1010-990, 5))}")
        print(f"SW Version: {(_ascii_be(r, 1015-990, 5))}")
        print(f"Number of connectors: {_u32_be(r, 1020-990)}")
        print(f"Connector type: {CONNECTOR_TYPE[r[1022-990]]}")
        print(f"Number of phases: {r[1023-990]}")
        print(f"L1 connected to: {r[1024-990]}")
        print(f"L2 connected to: {r[1025-990]}")
        print(f"L3 connected to: {r[1026-990]}")
        print(f"Custom max current: {_f32_be(r, 1028-990)} A")
        client.close()
        if evse['type'] == 'master':
            dev=ModbusDevice(evse["name"], evse["ip"], 503, timeout_s=2.0)
            client = dev.ensure_client()
            ok=client.connect()
            print(f"\n{evse["name"]} connected: {ok}\n")
            rr=_read_input_registers(client, address=3000, count=1, unit_id=1)
            r=rr.registers
            print(f"Loadguard installed: {r[0]}")
            rr=_read_input_registers(client, address=2000, count=26, unit_id=1)
            r=rr.registers
            print(f"LoadGuard connected: {r[0]}")
            print(f"Frequency: {_f32_be(r, 2002-2000):.2f} Hz")
            print(f"L1-N Voltage: {_f32_be(r, 2004-2000):.1f} V")
            print(f"L2-N Voltage: {_f32_be(r, 2006-2000):.1f} V")
            print(f"L3-N Voltage: {_f32_be(r, 2008-2000):.1f} V")
            print(f"L1 Current: {_f32_be(r, 2010-2000):.2f} A")
            print(f"L2 Current: {_f32_be(r, 2012-2000):.2f} A")
            print(f"L3 Current: {_f32_be(r, 2014-2000):.2f} A")
            print(f"Active power L 1: {_f32_be(r, 2016-2000):.2f} kW")
            print(f"Active power L 2: {_f32_be(r, 2018-2000):.2f} kW")
            print(f"Active power L 3: {_f32_be(r, 2020-2000):.2f} kW")
            print(f"Total power: {_f32_be(r, 2022-2000):.2f} kW")
            rr=_read_input_registers(client, address=2100, count=14, unit_id=1)
            r=rr.registers
            print(f"Power cluster Current L1: {_f32_be(r, 2100-2100):.2f} A")
            print(f"Power cluster Current L2: {_f32_be(r, 2102-2100):.2f} A")
            print(f"Power cluster Current L3: {_f32_be(r, 2104-2100):.2f} A")
            print(f"Power cluster Active power L1: {_f32_be(r, 2106-2100):.2f} kW")
            print(f"Power cluster Active power L2: {_f32_be(r, 2108-2100):.2f} kW")
            print(f"Power cluster Active power L3: {_f32_be(r, 2110-2100):.2f} kW")
            print(f"Power cluster Total power: {_f32_be(r, 2112-2100):.2f} kW")
            client.close()
    except Exception as e:
        print(f"Error reading {evse['name']}: {e}")