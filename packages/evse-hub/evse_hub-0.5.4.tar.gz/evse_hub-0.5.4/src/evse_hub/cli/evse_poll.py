from __future__ import annotations

import asyncio
import logging
import secrets

from .runtime import EndpointRuntime
from ..modbus.modbus_device import ModbusDevice, poll_modbus_async
from ..modbus.etrel.modbus_reads import read_master_loadguard, read_evse
from ..influx.influx_writes import write_influx_master, write_influx_evse
from ..tools.async_tools import run_blocking

log = logging.getLogger(__name__)

async def periodic_master_once(dev: ModbusDevice, secrets: dict) -> None:
    """Periodically poll master loadguard and write results to InfluxDB.
    
    Args:
        dev: ModbusDevice instance to poll.
        secrets: Dictionary of secrets for InfluxDB.
        period_s: Polling period in seconds.
    """
    try:
        data = await poll_modbus_async(dev, read_master_loadguard)
        if data is not None:
            await run_blocking(
                        write_influx_master,
                        secrets,
                        data,
                        dryrun=False,
                        timeout_s=4.0,
                    )
    except asyncio.CancelledError:
        # Task shutdown is expected (Ctrl-C / cancellation); exit quietly.
        raise
    
async def periodic_charger_once(dev: ModbusDevice, secrets: dict, evse_id: str) -> None:
    log.debug("Starting single charger poll for device: %s", dev.name)
    try:
        data = await poll_modbus_async(dev, read_evse)
        if data is not None:
            data["user"] = evse_id
            await run_blocking(write_influx_evse, secrets, data, dryrun=False, timeout_s=4.0)
       
    except asyncio.CancelledError:
        # Task shutdown is expected (Ctrl-C / cancellation); exit quietly.
        raise

async def poll_endpoint(rt: EndpointRuntime, secrets: dict) -> None:
    """
    Poll a single endpoint for its configured roles using the provided secrets.

    Args:
        rt (EndpointRuntime): The runtime state and configuration for the endpoint.
        secrets (dict): Secrets/configuration required for polling routines.
    Returns:
        None
    """
    try:
        while True:
            rt.active.set()
            try:
                async with rt.lock:
                    if "charger" in rt.cfg.roles:
                        await periodic_charger_once(rt.mb, secrets, evse_id=rt.cfg.evse_id)
                    if "master" in rt.cfg.roles:
                        await periodic_master_once(rt.mb, secrets)
            finally:
                rt.active.clear()
            await asyncio.sleep(rt.cfg.poll_period_s)
    except asyncio.CancelledError:
        log.debug("poll_endpoint CANCEL %s", rt.cfg.key)
        raise
    finally:
        log.debug("poll_endpoint END %s", rt.cfg.key)