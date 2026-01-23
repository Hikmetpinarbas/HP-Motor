from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class ProviderColumnSpec:
    canonical_key: str              # logical key like "x", "player_id", "xT"
    aliases: List[str]              # possible headers
    required: bool = False
    target: Optional[str] = None    # optional semantic target path (events.start_x etc)


class ProviderRegistry:
    """
    Loads provider mappings (YAML) for auto-discovery column mapping.
    """

    def __init__(self, mapping_path: Path):
        self.mapping_path = mapping_path
        self.provider_id = None
        self.description = None
        self.columns: Dict[str, ProviderColumnSpec] = {}

        self._load()

    def _load(self) -> None:
        data = yaml.safe_load(self.mapping_path.read_text(encoding="utf-8"))
        self.provider_id = data.get("provider_id")
        self.description = data.get("description")

        cols = data.get("columns", {}) or {}
        for canonical_key, spec in cols.items():
            aliases = spec.get("aliases", []) or []
            target = spec.get("target")
            required = bool(spec.get("required", False))
            self.columns[canonical_key] = ProviderColumnSpec(
                canonical_key=canonical_key,
                aliases=[str(a) for a in aliases],
                required=required,
                target=target,
            )

    def get_specs(self) -> Dict[str, ProviderColumnSpec]:
        return self.columns