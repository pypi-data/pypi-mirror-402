from __future__ import annotations
import logging
import os
import yaml


def load_secrets(path: str = "secrets.yaml") -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)
    
def setup_logging() -> None:
    level_name = os.getenv("LOGLEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(levelname)s:%(name)s:%(message)s",
    )

def read_env_variable(var_name: str, default: str | None = None) -> str:
    value = os.getenv(var_name, default)
    if value is None:
        raise EnvironmentError(f"Environment variable '{var_name}' is not set and no default value provided.")
    return value    