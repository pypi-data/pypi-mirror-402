# Copilot instructions for this repository

Purpose
- Provide concise, repository-specific guidance so an AI coding agent can be productive immediately.

Big picture
- This project is a small Python 3.11 daemon that polls Modbus/TCP devices and writes metrics to InfluxDB. See `src/poller/main.py` for the polling orchestration.
- Polling flow: `main.py` creates periodic tasks that call `poll_modbus_async` (in `src/poller/modbus_device.py`) -> `read_*` functions in `src/poller/modbus_reads.py` -> `write_influx_master` in `src/poller/influx_writes.py`.

Key files and responsibilities
- `src/poller/main.py`: application entrypoint and task orchestration (`periodic_master`).
- `src/poller/modbus_device.py`: `ModbusDevice` state, connection management, and exponential backoff logic.
- `src/poller/modbus_reads.py`: low-level Modbus register reads and helpers (e.g. `_f32_be`, `_read_input_registers`). Use these read functions as blocking callables passed to `poll_modbus_async`.
- `src/poller/influx_writes.py`: writes to two InfluxDB instances using keys from `secrets.yaml`.
- `src/poller/async_tools.py`: `run_blocking` helper; uses a shared `ThreadPoolExecutor` (`_EXECUTOR`). Prefer this helper for running blocking calls from async code.
- `src/poller/config.py`: `load_secrets(path)` reads YAML secrets; keys required by `influx_writes.py` are: `ha_ip`, `ha_influx_username`, `ha_influx_pwd`, `mons_ip`, `mons_influx_username`, `mons_influx_pwd`.
- `src/poller/wifi.py`: checks association via the `iw` tool; used to skip polls when Wi‑Fi is disconnected.

Conventions & patterns to follow
- Keep polling logic separate from transport-specific device state: add new device protocols by creating new `Device` classes and `poll_*` functions (see `ModbusDevice` as the pattern).
- Blocking I/O must be run through `run_blocking(...)` to avoid blocking the event loop. Example: `await run_blocking(write_influx_master, secrets, data, dryrun=True)` (see `main.py`).
- Read functions used by `poll_modbus_async` are synchronous and should accept `(client, unit) -> dict` and raise on error (see `read_master_loadguard`).
- Follow the backoff semantics in `modbus_device.py` if adding new polling helpers (respect `dev.next_ok_ts` and `dev.fail_count`).

Running & testing
- Python version: >=3.11 (declared in `pyproject.toml`).
- Recommended run (from repository root):

```bash
PYTHONPATH=src python -m poller.main
```

- Run tests (from repository root):

```bash
PYTHONPATH=src pytest -q
```

External dependencies & environment
- Code imports not listed in `pyproject.toml`: `pymodbus`, `influxdb` (the InfluxDBClient package), `pyyaml` is declared. Install with pip in a virtualenv as needed.
- `src/poller/wifi.py` requires the `iw` binary on the host.
- Secrets file: `secrets.yaml` (loaded by `src/poller/config.py`). Do not commit real credentials — the repo contains a placeholder `secrets.yaml` under `src/`.

Examples for common code changes
- Add a new Modbus read: implement a function `read_<device>(client, unit) -> dict` in `src/poller/modbus_reads.py` mirroring `read_master_loadguard`, then call it from `main.py` via `poll_modbus_async`.
- Add an output sink: create a new writer function (blocking) in `src/poller/influx_writes.py` or a new module; call it via `run_blocking` from async code. Respect `dryrun=True` for safe local testing.

Notes for AI agents
- Prefer minimal, focused diffs. Avoid wide refactors unless the change is necessary and accompanied by tests.
- When changing I/O or dependency usage, update `pyproject.toml` and document required system packages (e.g., `iw`) in the PR description.
- Use existing functions as canonical examples: `poll_modbus_async`, `read_master_loadguard`, `write_influx_master`, and `run_blocking`.

If anything in this guidance is unclear or you need more examples, ask for clarification and I will iterate.
