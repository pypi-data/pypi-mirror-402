from __future__ import annotations

import asyncio
import logging
from typing import Dict

from evse_hub.tools.config import load_secrets
from evse_hub.modbus.modbus_device import ModbusDevice, poll_modbus_async
from evse_hub.modbus.etrel.modbus_reads import read_master_loadguard
from evse_hub.influx.influx_writes import write_influx_master
from evse_hub.tools.async_tools import run_blocking

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


async def periodic_master(dev: ModbusDevice, secrets: dict, period_s: float) -> None:
    try:
        while True:
            data = await poll_modbus_async(dev, read_master_loadguard)
            if data is not None:
                await run_blocking(
                    write_influx_master,
                    secrets,
                    data,
                    dryrun=True,
                    timeout_s=5.0,
                )
            await asyncio.sleep(period_s)
    except asyncio.CancelledError:
        # Task shutdown is expected (Ctrl-C / cancellation); exit quietly.
        return


async def main() -> None:
    secrets = load_secrets("secrets.yml")

    mb_devices: Dict[str, ModbusDevice] = {
        "master_etrel": ModbusDevice("master_etrel", "192.168.1.121", 503, timeout_s=2.0),
    }

    tasks = [
        asyncio.create_task(
            periodic_master(mb_devices["master_etrel"], secrets, period_s=15.0),
            name="periodic_master",
        ),
    ]

    try:
        await asyncio.gather(*tasks)

    except asyncio.CancelledError:
        # If the event loop cancels us, proceed to cleanup.
        pass

    finally:
        log.info("Shutting down...")

        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        for d in mb_devices.values():
            d.close()

        log.info("Shutdown complete.")


def cli() -> None:
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    cli()