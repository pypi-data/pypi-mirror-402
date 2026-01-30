import asyncio
import logging
import os
from typing import Dict

from .evse_poll import poll_endpoint
from ..tools.device_config import EndpointCfg, load_endpoints_from_evses_yml
from ..cli.runtime import EndpointRuntime, stop_runtime, make_modbus
from ..cli.status import load_status_snapshot
from ..tools.config import load_secrets, setup_logging, read_env_variable


log = logging.getLogger(__name__)


async def supervisor(secrets: dict, endpoints: Dict[str, EndpointCfg], status_path: str) -> None:
    """
    Orchestrates the lifecycle of all endpoint runtime objects and manages their polling tasks.

    This function is responsible for:
    - Instantiating a runtime object for each endpoint, which encapsulates its configuration and Modbus client.
    - Entering a main event loop that runs indefinitely, checking every 2 seconds for changes in endpoint online status.
    - For each endpoint:
        * If the endpoint is online and not already being polled, it spawns an asynchronous polling coroutine (via poll_endpoint), which handles Modbus polling and InfluxDB writing for that endpoint.
        * If the endpoint goes offline and a polling task is active, it cancels the polling task and cleans up resources for that endpoint.
    - Ensures that only online endpoints are actively polled, and that offline endpoints do not consume resources.
    - Handles exceptions gracefully, logging errors and continuing the supervision loop without crashing.
    - On shutdown (when the coroutine is cancelled), it ensures all polling tasks are stopped and resources are cleaned up for all endpoints.

    Args:
        secrets (dict): Secrets/configuration for polling tasks (e.g., InfluxDB credentials).
        endpoints (Dict[str, EndpointCfg]): Mapping of endpoint keys to configuration objects.
        status_path (str): Path to the status snapshot JSON file, which determines endpoint online/offline state.
    Returns:
        None
    """

    runtimes: Dict[str, EndpointRuntime] = {
        key: EndpointRuntime(cfg=cfg, mb=make_modbus(cfg))
        for key, cfg in endpoints.items()
    }
    for key, rt in runtimes.items():
        log.info("endpoint=%s host=%s port=%s mb_id=%s",key, rt.cfg.host, rt.cfg.port, id(rt.mb))


    for key in runtimes:
        log.info("Supervisor managing endpoint: %s", key)

    try:
        while True:
            try:
                snap = load_status_snapshot(status_path)

                for key, rt in runtimes.items():
                    online = snap.online_by_id.get(rt.cfg.evse_id, False)
                    log.debug("Endpoint %s online status: %s", key, online)

                    if online and rt.task is None:
                        rt.online = True
                        rt.task = asyncio.create_task(
                            poll_endpoint(rt, secrets),
                            name=f"poll:{key}",
                        )
                        rt.task.add_done_callback(_log_task_result)

                    elif (not online) and rt.task is not None:
                        rt.online = False
                        await stop_runtime(rt)

                await asyncio.sleep(2.0)

            except asyncio.CancelledError:
                raise
            except Exception:
                # If anything goes wrong in one iteration, log it and keep going
                log.exception("Supervisor loop iteration failed (continuing)")
                await asyncio.sleep(2.0)

    finally:
        await asyncio.gather(*(stop_runtime(rt) for rt in runtimes.values()), return_exceptions=True)

def _log_task_result(t: asyncio.Task) -> None:
    """
    Callback to log the result of a polling task when it completes.

    Args:
        t (asyncio.Task): The asyncio Task whose result is being checked.
    Returns:
        None
    """
    try:
        exc = t.exception()
    except asyncio.CancelledError:
        return
    except Exception:
        log.exception("Failed to read task exception")
        return
    if exc is not None:
        log.error("Polling task %s crashed: %r", t.get_name(), exc, exc_info=exc)


def main() -> None:
    setup_logging()
    asyncio.run(_amain())

async def _amain() -> None:

    secrets_file=read_env_variable("SUPERVISOR_SECRETS_FILE", "secrets.yml")
    evse_file=read_env_variable("SUPERVISOR_EVSE_FILE", "evse.yml")
    status_file=read_env_variable("SUPERVISOR_STATUS_FILE", "status.json")

    secrets = load_secrets(secrets_file)
    endpoints = load_endpoints_from_evses_yml(evse_file)
    await supervisor(secrets, endpoints, status_path=status_file)

if __name__ == "__main__":
    try:
        main()   
    except KeyboardInterrupt:
        pass