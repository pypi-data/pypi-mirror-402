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