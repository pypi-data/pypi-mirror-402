# tools/device_config.py
from __future__ import annotations
import yaml
from typing import Dict, FrozenSet
from dataclasses import dataclass
from .config import read_env_variable


@dataclass(frozen=True)
class EndpointCfg:
    key: str                  # unique key
    evse_id: str              # str(unit_id) used for status.json join
    name: str                 # human name
    host: str
    port: int
    unit: int = 1
    timeout_s: float = 2.0
    roles: FrozenSet[str] = frozenset({"charger"})
    poll_period_s: float = float(read_env_variable("EVSE_POLL_PERIOD_S", "15.0"))


def load_endpoints_from_evses_yml(path: str) -> Dict[str, EndpointCfg]:
    doc = yaml.safe_load(open(path, "r"))
    endpoints: Dict[str, EndpointCfg] = {}

    for d in doc.get("devices", []):
        name = d["name"]
        host = d["ip"]
        evse_id = str(d["unit_id"])
        typ = d.get("type", "client")

        # always poll charger endpoint on 502
        key_502 = f"{name}:502"
        endpoints[key_502] = EndpointCfg(
            key=key_502,
            evse_id=evse_id,
            name=name,
            host=host,
            port=502,
            roles=frozenset({"charger"}),
        )

        # master additionally polled on 503
        if typ == "master":
            key_503 = f"{name}:503"
            endpoints[key_503] = EndpointCfg(
                key=key_503,
                evse_id=evse_id,
                name="master",
                host=host,
                port=503,
                roles=frozenset({"master"}),
            )

    return endpoints
