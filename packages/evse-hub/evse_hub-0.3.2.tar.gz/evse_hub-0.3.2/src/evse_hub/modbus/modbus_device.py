from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional, Any

from pymodbus.client import ModbusTcpClient

from ..tools.wifi import wifi_is_associated
from ..tools.async_tools import run_blocking

log = logging.getLogger(__name__)


@dataclass
class ModbusDevice:
    """
    A Modbus/TCP endpoint + polling backoff state.

    Keep this intentionally Modbus-specific. If/when you add MQTT or HTTP-polled
    devices, create separate *Device + poll_* functions rather than overloading
    this class with protocol-specific fields.
    """
    name: str
    host: str
    port: int
    unit: int = 1
    timeout_s: float = 2.0

    client: Optional[ModbusTcpClient] = None
    next_ok_ts: float = 0.0
    fail_count: int = 0

    def ensure_client(self) -> ModbusTcpClient:
        if self.client is None:
            self.client = ModbusTcpClient(self.host, port=self.port, timeout=self.timeout_s)
        return self.client

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.close()
            except Exception:
                pass
        self.client = None


async def poll_modbus_async(
    dev: ModbusDevice,
    read_fn: Callable[..., dict],
    *args: Any,
    wifi_if: str = "wlan0",
    **kwargs: Any,
) -> Optional[dict]:
    """
    Poll a Modbus device with exponential backoff, returning measurements on success.

    `read_fn` is your existing blocking block-read function:
        read_fn(client: ModbusTcpClient, unit: int) -> dict
    """
    now = time.time()
    if now < dev.next_ok_ts:
        return None

    if wifi_if:
        associated = await run_blocking(wifi_is_associated, wifi_if, timeout_s=1.5)
        if not associated:
            log.warning("Wi-Fi %s not associated; skipping poll for %s", wifi_if, dev.name)
            # Try again soon; don't "punish" the device with exponential backoff.
            dev.next_ok_ts = now + 2.0
            return None

    client = dev.ensure_client()

    try:
        ok = await run_blocking(client.connect, timeout_s=dev.timeout_s + 1.0)
        if not ok:
            raise RuntimeError("connect failed")

        data = await run_blocking(read_fn, client, dev.unit, *args, **kwargs, timeout_s=dev.timeout_s + 2.0)

        dev.fail_count = 0
        dev.next_ok_ts = now
        return data

    except Exception as e:
        dev.fail_count += 1
        backoff = min(60, 2 ** min(dev.fail_count, 6))
        dev.next_ok_ts = now + backoff
        log.warning("%s poll failed (%s). backoff=%ss", dev.name, e, backoff)
        dev.close()
        return None