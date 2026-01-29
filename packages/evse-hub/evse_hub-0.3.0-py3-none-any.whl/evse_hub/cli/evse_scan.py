#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import ipaddress
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class HostResult:
    ip: str
    port_502_open: bool


async def check_tcp_port(ip: str, port: int, timeout_s: float) -> bool:
    """
    True if TCP connect succeeds within timeout.
    """
    try:
        conn = asyncio.open_connection(ip, port)
        reader, writer = await asyncio.wait_for(conn, timeout=timeout_s)
        writer.close()
        # Python 3.11+: wait_closed exists for StreamWriter
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except (asyncio.TimeoutError, OSError):
        return False


async def scan_modbus_502_async(
    cidr: str = "192.168.1.0/24",
    timeout_s: float = 0.35,
    concurrency: int = 400,
) -> List[HostResult]:
    net = ipaddress.ip_network(cidr, strict=False)
    ips = [str(ip) for ip in net.hosts()]

    sem = asyncio.Semaphore(concurrency)

    async def one(ip: str) -> HostResult:
        async with sem:
            ok = await check_tcp_port(ip, 502, timeout_s)
            return HostResult(ip=ip, port_502_open=ok)

    results = await asyncio.gather(*(one(ip) for ip in ips))
    hits = [r for r in results if r.port_502_open]
    hits.sort(key=lambda r: ipaddress.ip_address(r.ip))
    return hits


def main() -> None:
    async def _main_async() -> None:
        
        hits = await scan_modbus_502_async()
        if not hits:
            print("No hosts with TCP/502 open found in 192.168.1.0/24")
            return

        print("Hosts with TCP/502 open:")
        for h in hits:
            print(f"  {h.ip}:502")

    try:
        asyncio.run(_main_async())
    except KeyboardInterrupt:
        # asyncio signal handlers should already set the stop event; ensure exit
        print("Interrupted by user; exiting")


if __name__ == "__main__":
    main()
