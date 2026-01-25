from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _find_repo_root(start: Path, max_hops: int = 12) -> Optional[Path]:
    cur = start.resolve()
    for _ in range(max_hops):
        if (cur / "pyproject.toml").exists() or (cur / ".git").exists() or (cur / "README.md").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return None


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_canon_index() -> Dict[str, Any]:
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    if repo_root is None:
        return {}
    idx = repo_root / "canon" / "index.yaml"
    if not idx.exists():
        return {}
    try:
        return _load_yaml(idx)
    except Exception:
        return {}


def load_engine_metrics_from_registry() -> Dict[str, Any]:
    """
    Engine registry format (list-based):
      metrics:
        - canonical_name: PPDA
          ...
    Output normalized to dict keyed by canonical_name (upper snake-ish)
    """
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    if repo_root is None:
        return {}

    idx = load_canon_index()
    sources = (idx or {}).get("sources", {}) or {}
    primary = (sources.get("primary_engine") or {}) if isinstance(sources, dict) else {}
    reg_root = primary.get("engine_registry_root", "canon/engine_registry")
    reg_path = repo_root / reg_root / "metrics_core_v1.yaml"

    if not reg_path.exists():
        return {}

    try:
        data = _load_yaml(reg_path)
    except Exception:
        return {}

    out: Dict[str, Any] = {}
    metrics = (data or {}).get("metrics")
    if isinstance(metrics, list):
        for m in metrics:
            if not isinstance(m, dict):
                continue
            key = (m.get("canonical_name") or m.get("metric_id") or m.get("id") or "").strip()
            if key:
                out[key] = m
    elif isinstance(metrics, dict):
        # already keyed
        for k, v in metrics.items():
            if isinstance(k, str) and k.strip():
                out[k.strip()] = v
    return out


def load_legacy_motor_metrics() -> Dict[str, Any]:
    """
    Legacy fallback:
      HP-Motor-main/canon/registry.json
    """
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    if repo_root is None:
        return {}

    reg = repo_root / "canon" / "registry.json"
    if not reg.exists():
        return {}

    try:
        data = _load_json(reg)
    except Exception:
        return {}

    metrics: Dict[str, Any] = {}
    if isinstance(data, dict):
        m = data.get("metrics", data)
        if isinstance(m, dict):
            metrics.update(m)
        elif isinstance(m, list):
            for obj in m:
                if isinstance(obj, dict):
                    mid = (obj.get("metric_id") or obj.get("id") or "").strip()
                    if mid:
                        metrics[mid] = obj
    return metrics


def load_canon_metrics() -> Dict[str, Any]:
    """
    Unified canon metrics:
      1) Engine registry metrics_core_v1.yaml (primary)
      2) Legacy motor canon/registry.json (fallback)
    """
    engine = load_engine_metrics_from_registry()
    legacy = load_legacy_motor_metrics()

    # Engine is primary; legacy fills gaps only
    merged = dict(legacy)
    merged.update(engine)
    return merged


def load_contracts() -> Dict[str, Any]:
    """
    Returns canonical contracts referenced in canon/index.yaml.
    """
    repo_root = _find_repo_root(Path(__file__).resolve().parent)
    if repo_root is None:
        return {}

    idx = load_canon_index()
    contracts = (idx or {}).get("contracts", {}) or {}
    out: Dict[str, Any] = {"index": idx, "contracts": contracts}

    # Load optional schemas if present
    for k in ["universal_signal_schema", "analysis_claim_schema"]:
        rel = contracts.get(k)
        if isinstance(rel, str) and rel.strip():
            p = repo_root / rel
            if p.exists() and p.suffix.lower() == ".json":
                try:
                    out[k] = _load_json(p)
                except Exception:
                    out[k] = {"_error": f"failed to load {rel}"}

    return out