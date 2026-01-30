from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

SDCARD_ROOT = Path("/sdcard/HP_LIBRARY")

@dataclass(frozen=True)
class LibraryHealth:
    status: str
    flags: List[str]
    roots_checked: List[str]

def _project_root() -> Path:
    return Path(__file__).resolve().parent

def _roots() -> List[Path]:
    return [_project_root(), SDCARD_ROOT]

def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _resolve(rel: str) -> Tuple[Path | None, LibraryHealth]:
    flags: List[str] = []
    checked: List[str] = []
    for r in _roots():
        checked.append(str(r))
        p = r / rel
        if p.exists() and p.is_file():
            return p, LibraryHealth(status="OK", flags=[], roots_checked=checked)
    flags.append(f"missing_artifact:{rel}")
    return None, LibraryHealth(status="DEGRADED", flags=flags, roots_checked=checked)

def load_registry() -> Tuple[Dict[str, Any], LibraryHealth]:
    p, h = _resolve("registry/metric_registry.json")
    if not p:
        return {"metrics": [], "version": "missing"}, h
    return _read_json(p), h

def load_vendor_mappings() -> Tuple[Dict[str, Any], LibraryHealth]:
    p, h = _resolve("registry/vendor_mappings.json")
    if not p:
        return {"vendor": {}, "version": "missing"}, h
    return _read_json(p), h
