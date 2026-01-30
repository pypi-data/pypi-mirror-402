# heartbeat.py
from __future__ import annotations

import asyncio
import socket
import logging
import time
import functools
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    # InfluxDB 1.x official client
    from influxdb import InfluxDBClient
except ImportError as e:  # pragma: no cover
    raise ImportError("Install influxdb (InfluxDB 1.x client): pip install influxdb") from e

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _now_ts_s() -> int:
    return int(time.time())


def _default_host() -> str:
    # hostname for tags
    return socket.gethostname()


def make_influxdb_client_18(
    *,
    host: str,
    port: int = 8086,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    ssl: bool = False,
    verify_ssl: bool = True,
    timeout_s: float = 5.0,
) -> InfluxDBClient:
    """
    Small helper to standardize client creation for InfluxDB 1.8.
    """
    return InfluxDBClient(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
        ssl=ssl,
        verify_ssl=verify_ssl,
        timeout=timeout_s,
    )


@dataclass(frozen=True, slots=True)
class HeartbeatConfig:
    """
    Configuration for heartbeat points.

    - service: required logical daemon/service name
    - version: required version string (e.g. git tag, semver, setuptools-scm)
    - host: default hostname if not set
    - measurement: defaults to "heartbeat"
    """
    service: str
    version: str
    host: str = ""
    measurement: str = "heartbeat"

    def normalized_host(self) -> str:
        return self.host or _default_host()


class Heartbeat:
    """
    Reusable heartbeat emitter for InfluxDB 1.8.

    Emits points with payload grammar:

    {
        "measurement": "heartbeat",
        "fields": {"alive": 1/0, "start_ts": <epoch seconds>},
        "tags": {"host": "...", "service": "...", "version": "..."}
    }

    Notes:
    - start_ts is the daemon start time, captured once at construction by default.
    - alive=1 for normal beats; alive=0 can be used for a final "going down" point.
    """

    def __init__(
        self,
        client: InfluxDBClient,
        cfg: HeartbeatConfig,
        *,
        start_ts: Optional[int] = None,
        executor: Optional[ThreadPoolExecutor] = None,
        owns_client: bool = False,
        owns_executor: bool = False,
    ) -> None:
        self._client = client
        self._cfg = cfg
        self._start_ts = _now_ts_s() if start_ts is None else int(start_ts)
        self._executor = executor  # optional bounded executor for async writes
        self._owns_client = owns_client
        self._owns_executor = owns_executor
        self._closed = False

    def close(self) -> None:
        """Close owned resources (idempotent)."""
        if self._closed:
            return
        self._closed = True

        if self._owns_executor and self._executor is not None:
            self._executor.shutdown(wait=False, cancel_futures=True)
            self._executor = None

        if self._owns_client and self._client is not None:
            try:
                self._client.close()  # influxdb client has close()
            except Exception:
                pass
    
    def __enter__(self) -> "Heartbeat":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    async def __aenter__(self) -> "Heartbeat":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        # executor shutdown is sync; do it in a thread so it doesn't block loop
        await asyncio.to_thread(self.close)

    @property
    def start_ts(self) -> int:
        return self._start_ts

    def payload(self, *, alive: int) -> Dict[str, Any]:
        """
        Build the payload dict EXACTLY matching your grammar.
        """
        alive_i = int(alive)
        if alive_i not in (0, 1):
            raise ValueError("alive must be 0 or 1")

        return {
            "measurement": self._cfg.measurement,
            "fields": {
                "alive": alive_i,
                "start_ts": int(self._start_ts),
            },
            "tags": {
                "host": self._cfg.normalized_host(),
                "service": self._cfg.service,
                "version": self._cfg.version,
            },
        }

    # -------- Sync API --------

    def write(self, *, alive: int = 1, time_precision: str = "s") -> bool:
        """
        Synchronously write a single heartbeat point.
        Returns True on success, False on failure.
        """
        point = self.payload(alive=alive)
        try:
            # influxdb client expects a list of points
            return bool(self._client.write_points([point], time_precision=time_precision))
        except Exception:
            log.debug("Heartbeat write failed", exc_info=True)
            return False

    # -------- Async API --------

    async def write_async(self, *, alive: int = 1, time_precision: str = "s") -> bool:
        """
        asyncio-friendly write using either:
        - provided bounded executor, or
        - asyncio.to_thread fallback
        """
        point = self.payload(alive=alive)

        try:
            fn = functools.partial(self._client.write_points, [point], time_precision=time_precision)

            if self._executor is not None:
                log.debug("Using custom executor for heartbeat write")
                loop = asyncio.get_running_loop()
                
                return bool(
                    await loop.run_in_executor(
                        self._executor,
                        fn,
                    )
                )       
                        
            log.debug("Using asyncio.to_thread for heartbeat write")
            # Fallback: uses default thread pool
            return bool(
                await asyncio.to_thread(fn)
            )
        except Exception:
            log.debug("Heartbeat write_async failed", exc_info=True)
            return False

    @classmethod
    def create_with_influxdb(
        cls,
        *,
        host: str,
        database: str,
        service: str,
        version: str,
        username: str,
        password: str,
        timeout_s: float = 3.0,
        max_workers: int = 1,
    ) -> "Heartbeat":
        """
        Factory method to create a Heartbeat instance with InfluxDB client.
        
        Args:
            host: InfluxDB host address
            database: InfluxDB database name
            service: Service name for heartbeat
            version: Service version
            username: InfluxDB username
            password: InfluxDB password
            timeout_s: InfluxDB connection timeout in seconds
            max_workers: ThreadPoolExecutor max workers
        
        Returns:
            Initialized Heartbeat instance
        """
        client = make_influxdb_client_18(
            host=host,
            database=database,
            timeout_s=timeout_s,
            username=username,
            password=password
        )
        executor = ThreadPoolExecutor(max_workers=max_workers)
        
        return cls(
            client,
            HeartbeatConfig(service=service, version=version),
            executor=executor,
            owns_client=True,
            owns_executor=True,
        )



