from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from hp_motor.ingest.provider_registry import ProviderRegistry


@dataclass
class MappingHit:
    canonical_key: str
    source_column: Optional[str]
    required: bool
    status: str  # HIT | MISS


class CanonicalMapper:
    """
    Auto-map incoming dataframe headers to canonical keys using ProviderRegistry.
    Strategy:
      - Case-insensitive header matching
      - Alias matching
      - Does NOT drop rows
      - Produces mapping report + optionally renames df columns
    """

    def __init__(self, provider_registry: ProviderRegistry):
        self.provider_registry = provider_registry

    def map_df(self, df: pd.DataFrame, rename: bool = True) -> Tuple[pd.DataFrame, Dict]:
        specs = self.provider_registry.get_specs()

        # Build lookup: normalized header -> actual header
        header_map = {self._norm(c): c for c in df.columns}

        hits: List[MappingHit] = []
        rename_map: Dict[str, str] = {}
        missing_required: List[str] = []

        for canonical_key, spec in specs.items():
            found_col = None
            # Try direct canonical_key name
            if self._norm(canonical_key) in header_map:
                found_col = header_map[self._norm(canonical_key)]
            else:
                # Try aliases
                for a in spec.aliases:
                    if self._norm(a) in header_map:
                        found_col = header_map[self._norm(a)]
                        break

            if found_col is None:
                hits.append(MappingHit(canonical_key, None, spec.required, "MISS"))
                if spec.required:
                    missing_required.append(canonical_key)
            else:
                hits.append(MappingHit(canonical_key, found_col, spec.required, "HIT"))
                # rename source column -> canonical_key
                if rename and found_col != canonical_key:
                    rename_map[found_col] = canonical_key

        out_df = df.rename(columns=rename_map) if rename_map else df

        report = {
            "provider_id": self.provider_registry.provider_id,
            "mapping_hits": [h.__dict__ for h in hits],
            "rename_map": rename_map,
            "missing_required": missing_required,
            "ok": len(missing_required) == 0,
        }
        return out_df, report

    def _norm(self, s: str) -> str:
        return str(s).strip().lower()