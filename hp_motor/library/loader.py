from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple


SDCARD_ROOT = Path("/sdcard/HP_LIBRARY")


@dataclass(frozen=True)
class LibraryHealth:
    status: str  # OK | DEGRADED
    flags: List[str]
    roots_checked: List[str]


def _project_library_root() -> Path:
    # hp_motor/library
    return Path(__file__).resolve().parent


def _roots() -> List[Path]:
    return [
        _project_library_root(),  # hp_motor/library
        SDCARD_ROOT,              # /sdcard/HP_LIBRARY
    ]


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve(rel: str) -> Tuple[Path | None, LibraryHealth]:
    checked: List[str] = []
    for r in _roots():
        checked.append(str(r))
        p = r / rel
        if p.exists() and p.is_file():
            return p, LibraryHealth(status="OK", flags=[], roots_checked=checked)

    # Not found anywhere
    return None, LibraryHealth(
        status="DEGRADED",
        flags=[f"missing_artifact:{rel}"],
        roots_checked=checked,
    )


def load_registry() -> Tuple[Dict[str, Any], LibraryHealth]:
    p, h = _resolve("registry/metric_registry.json")
    if not p:
        return {"version": "missing", "metrics": []}, h
    return _read_json(p), h


def load_vendor_mappings() -> Tuple[Dict[str, Any], LibraryHealth]:
    p, h = _resolve("registry/vendor_mappings.json")
    if not p:
        return {"version": "missing", "vendor": {}}, h
    return _read_json(p), h


def library_health() -> LibraryHealth:
    # Aggregate health across required artifacts
    _, h1 = _resolve("registry/metric_registry.json")
    _, h2 = _resolve("registry/vendor_mappings.json")

    flags = list(dict.fromkeys(h1.flags + h2.flags))
    status = "OK" if not flags else "DEGRADED"
    return LibraryHealth(status=status, flags=flags, roots_checked=h1.roots_checked)
