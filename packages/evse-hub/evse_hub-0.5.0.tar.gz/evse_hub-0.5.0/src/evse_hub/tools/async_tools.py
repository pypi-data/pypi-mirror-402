from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

# Small, shared pool for all blocking work (modbus + influx + subprocess).
# Tune max_workers if you add many devices; 4–8 is typically plenty here.
_EXECUTOR = ThreadPoolExecutor(max_workers=4)


async def run_blocking(fn: Callable[..., Any], /, *args: Any, timeout_s: float | None = None, **kwargs: Any) -> Any:
    """
    Run a blocking function in a bounded thread pool, optionally with a timeout.

    This is a thin wrapper around loop.run_in_executor (aka to_thread with control).
    """
    loop = asyncio.get_running_loop()

    def _call():
        return fn(*args, **kwargs)

    if timeout_s is None:
        return await loop.run_in_executor(_EXECUTOR, _call)

    async with asyncio.timeout(timeout_s):
        return await loop.run_in_executor(_EXECUTOR, _call)
