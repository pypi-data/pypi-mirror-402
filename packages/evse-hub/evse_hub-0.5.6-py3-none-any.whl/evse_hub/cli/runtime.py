from dataclasses import dataclass, field


import asyncio
import logging
from typing import Optional
from ..tools.device_config import EndpointCfg
from ..modbus.modbus_device import ModbusDevice

log = logging.getLogger(__name__)

@dataclass
class EndpointRuntime:
    """
    Holds runtime state for a single Modbus endpoint.

    Attributes:
        cfg: Endpoint configuration (EndpointCfg).
        mb: ModbusDevice instance for communication.
        lock: Asyncio lock for synchronizing access.
        active: Asyncio event indicating if endpoint is active.
        task: Optional asyncio Task for background operations.
        online: Boolean indicating if the endpoint is currently online.
    """
    cfg: EndpointCfg
    mb: ModbusDevice
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    active: asyncio.Event = field(default_factory=asyncio.Event)
    task: Optional[asyncio.Task] = None
    online: bool = False

async def stop_runtime(rt: EndpointRuntime) -> None:
    """
    Stop the polling task for a runtime and close its Modbus connection.

    Args:
        rt: EndpointRuntime instance to stop.
    """
    t = rt.task
    if t is None:
        log.debug("stop_runtime(%s): no task", rt.cfg.key)
        return

    log.debug("stop_runtime(%s): cancelling task %s done=%s", rt.cfg.key, t.get_name(), t.done())
    t.cancel()

    # Close early (under the same lock used by polling) to break blocking socket ops.
    async with rt.lock:
        rt.mb.close()

    try:
        await asyncio.wait_for(t, timeout=3.0)
    except asyncio.TimeoutError:
        log.warning("stop_runtime(%s): cancel timed out; background thread still running", rt.cfg.key)
    except asyncio.CancelledError:
        pass
    finally:
        rt.task = None
        log.debug("stop_runtime(%s): task cleared + mb closed", rt.cfg.key)

def make_modbus(cfg: EndpointCfg) -> ModbusDevice:
    """
    Create a ModbusDevice instance from an EndpointCfg.

    Args:
        cfg: EndpointCfg object with connection parameters.

    Returns:
        ModbusDevice instance.
    """
    return ModbusDevice(cfg.key, cfg.host, cfg.port, unit=cfg.unit, timeout_s=cfg.timeout_s)

