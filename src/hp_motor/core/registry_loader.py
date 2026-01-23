from __future__ import annotations

import os
from typing import Any, Dict

import yaml


def load_master_registry() -> Dict[str, Any]:
    """
    SSOT: src/hp_motor/registries/master_registry.yaml
    """
    here = os.path.dirname(os.path.abspath(__file__))
    reg_path = os.path.join(here, "..", "registries", "master_registry.yaml")
    reg_path = os.path.normpath(reg_path)

    with open(reg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}