#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# Locations/configurable via environment (useful for systemd unit files)
EVSE_YML = Path(os.getenv("EVSE_YML", "evse.yml"))
STATUS_JSON = Path(os.getenv("STATUS_JSON", "status.json"))

# Configure logging from environment (default INFO). Example: LOG_LEVEL=DEBUG
LOG_LEVEL_NAME = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL_NAME)
logger = logging.getLogger(__name__)

# If set to a level name (e.g. INFO, DEBUG), and the logger's level is
# at least that verbose, the status.json payload will also be written to
# the logger at INFO level. Leave unset to disable.
_status_level_name = os.getenv("WRITE_STATUS_TO_INFO_LEVEL", "")
WRITE_STATUS_TO_INFO_LEVEL: int | None = None
if _status_level_name:
    try:
        WRITE_STATUS_TO_INFO_LEVEL = logging._nameToLevel.get(_status_level_name.upper())
    except Exception:
        WRITE_STATUS_TO_INFO_LEVEL = None

PORT = 502

# Connect behavior
CONNECT_TIMEOUT_S = 0.45
RETRY_ONCE_DELAY_S_RANGE = (0.08, 0.25)  # jitter before the retry attempt

# Scheduler behavior
# How often to re-check *online* devices. Configurable via env var
# `EVSE_POLL_INTERVAL_S` (seconds). Default: 3600 (1 hour).
try:
    BASE_OK_INTERVAL_S = float(os.getenv("EVSE_POLL_INTERVAL_S", "3600"))
except Exception:
    BASE_OK_INTERVAL_S = 3600.0
if BASE_OK_INTERVAL_S <= 0:
    raise ValueError("EVSE_POLL_INTERVAL_S must be a positive number of seconds")

BASE_FAIL_INTERVAL_S = 60.0              # initial re-check interval after first failure
MAX_FAIL_INTERVAL_S = 300.0             # cap offline backoff at 5 minutes
JITTER_FRACTION = 0.15                  # +/- 15% jitter on scheduling

# Concurrency limit (even if you have many devices)
CONCURRENCY = 50


@dataclass
class DeviceState:
    unit_id: int
    name: str
    ip: Optional[str] = None

    online: bool = False
    fails: int = 0                    # consecutive failures
    next_check_ts: float = 0.0        # monotonic time when to check next


def _with_jitter(seconds: float, frac: float = JITTER_FRACTION) -> float:
    """
    Apply multiplicative jitter: seconds * U(1-frac, 1+frac)
    """
    lo = max(0.0, 1.0 - frac)
    hi = 1.0 + frac
    return seconds * random.uniform(lo, hi)


async def tcp_connect_ok(ip: str, port: int, timeout_s: float) -> bool:
    """
    True if TCP connect succeeds within timeout; closes immediately.
    """
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout_s)
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except (asyncio.TimeoutError, OSError):
        return False


async def check_with_retry(ip: str) -> bool:
    """
    Try once; if it fails, wait a small jittered delay and try once more.
    """
    ok = await tcp_connect_ok(ip, PORT, CONNECT_TIMEOUT_S)
    if ok:
        return True

    await asyncio.sleep(random.uniform(*RETRY_ONCE_DELAY_S_RANGE))
    return await tcp_connect_ok(ip, PORT, CONNECT_TIMEOUT_S)


def load_devices(path: Path) -> List[Tuple[int, str, Optional[str]]]:
    """
    Returns list of (unit_id, name, ip) from evse.yml devices.
    `ip` may be `None` when not present in the YAML; such devices will be
    included in the returned list but not actively checked.
    """
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("evse.yml root must be a mapping/dict")

    devices = data.get("devices", [])
    if not isinstance(devices, list):
        raise ValueError("evse.yml: 'devices' must be a list")

    out: List[Tuple[int, str, Optional[str]]] = []
    for d in devices:
        if not isinstance(d, dict):
            continue
        unit_id = d.get("unit_id")
        name = d.get("name")
        ip = d.get("ip")
        if isinstance(unit_id, int) and isinstance(name, str):
            out.append((unit_id, name, ip if isinstance(ip, str) else None))
    return out


def compute_next_interval(online: bool, fails: int) -> float:
    """
    Online: check every BASE_OK_INTERVAL_S.
    Offline: exponential backoff starting at BASE_FAIL_INTERVAL_S, doubling per consecutive failure,
             capped at MAX_FAIL_INTERVAL_S.
    """
    if online:
        return BASE_OK_INTERVAL_S
    # fails is >= 1 here
    interval = BASE_FAIL_INTERVAL_S * (2 ** max(0, fails - 1))
    interval = min(interval, MAX_FAIL_INTERVAL_S)
    return interval


def write_status_json(path: Path, states: Dict[int, DeviceState]) -> Dict[str, Any]:
    """
    Writes:
      {
        "ts": <unix>,
        "<unit_id>": {"online": true/false},
        ...
      }
    """
    payload: Dict[str, Any] = {"ts": int(time.time())}
    for unit_id in sorted(states.keys()):
        payload[str(unit_id)] = {"online": bool(states[unit_id].online)}
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return payload


async def poll_loop(stop_event: asyncio.Event) -> None:
    # Load config once at start (easy to add reload-on-change later)
    devs = load_devices(EVSE_YML)
    if not devs:
        raise SystemExit("No devices found under 'devices:' in evse.yml")

    # Create state per unit_id
    states: Dict[int, DeviceState] = {}
    now_mono = asyncio.get_running_loop().time()
    for unit_id, name, ip in devs:
        states[unit_id] = DeviceState(
            unit_id=unit_id,
            name=name,
            ip=ip,
            online=False,
            fails=0,
            next_check_ts=now_mono + random.uniform(0.0, 1.0) if ip is not None else float("inf"),  # small initial jitter
        )

    sem = asyncio.Semaphore(CONCURRENCY)

    async def check_one(st: DeviceState) -> None:
        # If the device has no IP configured, never attempt to check it.
        if st.ip is None:
            logger.info("Skipping device %d (%s): no IP configured", st.unit_id, st.name)
            st.online = False
            st.fails = 0
            st.next_check_ts = float("inf")
            return
        async with sem:
            logger.info("Checking device %d (%s) at %s", st.unit_id, st.name, st.ip)
            ok = await check_with_retry(st.ip)

        if ok:
            st.online = True
            st.fails = 0
        else:
            st.online = False
            st.fails += 1

        interval = compute_next_interval(st.online, max(1, st.fails) if not st.online else 0)
        interval = _with_jitter(interval)
        st.next_check_ts = asyncio.get_running_loop().time() + interval
        # Log result and scheduling
        ts_human = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        logger.info(
            "%s: Device %d (%s) -> %s; next check in %.1fs",
            ts_human,
            st.unit_id,
            st.name,
            "online" if st.online else "offline",
            interval,
        )

    # Main scheduler loop
    while not stop_event.is_set():
        loop = asyncio.get_running_loop()
        now = loop.time()

        due = [st for st in states.values() if st.next_check_ts <= now]
        if due:
            # Kick all due checks concurrently
            ids = ",".join(str(st.unit_id) for st in due)
            logger.info("Polling %d due devices: %s", len(due), ids)
            await asyncio.gather(*(check_one(st) for st in due))

            # Update status.json after each batch of checks
            payload = write_status_json(STATUS_JSON, states)

            # Optionally also write the payload to the logger at INFO
            # when the configured level is enabled (useful for CI/debug).
            if WRITE_STATUS_TO_INFO_LEVEL is not None and logger.isEnabledFor(WRITE_STATUS_TO_INFO_LEVEL):
                logger.info("status.json: %s", json.dumps(payload, sort_keys=True))

        # Sleep until the next device is due (or a short minimum to avoid busy loop)
        next_due = min(st.next_check_ts for st in states.values())
        sleep_s = max(0.1, next_due - loop.time())

        # Wait either for the sleep to finish or for a shutdown signal
        sleep_task = asyncio.create_task(asyncio.sleep(sleep_s))
        stop_task = asyncio.create_task(stop_event.wait())
        done, pending = await asyncio.wait({sleep_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
        for p in pending:
            p.cancel()

    # On shutdown request, write one final status snapshot
    try:
        payload = write_status_json(STATUS_JSON, states)
        if WRITE_STATUS_TO_INFO_LEVEL is not None and logger.isEnabledFor(WRITE_STATUS_TO_INFO_LEVEL):
            logger.info("final status.json: %s", json.dumps(payload, sort_keys=True))
    except Exception:
        logger.exception("Failed writing final status.json")


def main() -> None:
    # Create an asyncio event and attach signal handlers for graceful shutdown
    async def _main_async() -> None:
        loop = asyncio.get_running_loop()
        stop_event = asyncio.Event()

        # Register handlers to set the stop event on SIGINT/SIGTERM
        try:
            loop.add_signal_handler(signal.SIGINT, stop_event.set)
            loop.add_signal_handler(signal.SIGTERM, stop_event.set)
        except NotImplementedError:
            # Some platforms (or Python runtimes) may not support add_signal_handler
            pass

        await poll_loop(stop_event)

    try:
        asyncio.run(_main_async())
    except KeyboardInterrupt:
        # asyncio signal handlers should already set the stop event; ensure exit
        logger.info("Interrupted by user; exiting")


if __name__ == "__main__":
    main()
