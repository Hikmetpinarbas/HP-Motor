from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
import pandas as pd

from hp_motor.config.loader import load_spec
from hp_motor.ingest.loader import load_table
from hp_motor.integrity.popper import PopperGate
from hp_motor.engine.extract import extract_team_metrics
from hp_motor.diagnostics.dictionary import load_dictionary, build_alias_map
from hp_motor.diagnostics.inventory import load_inventory, allowed_sheets_for_corr

def _find_source_file(base_dir: Path, rel_path: str) -> Path | None:
    # spec'teki path genelde dosya adıdır; base_dir içinde ararız
    cand = base_dir / rel_path
    if cand.exists():
        return cand
    # fallback: sadece file name ile ara
    name = Path(rel_path).name
    hits = list(base_dir.rglob(name))
    return hits[0] if hits else None

def run(spec_path: str, base_dir: str, out_path: str, team_names: list[str]) -> Dict[str, Any]:
    spec = load_spec(spec_path)
    base = Path(base_dir)

    dict_path = base / "hp_motor/data/metric_dictionary.csv"
    inv_path  = base / "hp_motor/data/data_inventory.csv"

    # dictionary/inventory optional (yoksa degrade)
    dict_df = load_dictionary(str(dict_path)) if dict_path.exists() else None
    inv_df  = load_inventory(str(inv_path)) if inv_path.exists() else None

    report: Dict[str, Any] = {
        "hp_motor_version": spec.get("hp_motor_version"),
        "project": spec.get("project"),
        "sources": [],
        "teams": {},
        "degraded": []
    }

    # 1) sources: event csv'yi bul ve yükle
    event_sources = [s for s in spec.get("ingest", {}).get("sources", []) if s.get("grain_hint") == "event" and s.get("type") == "csv"]
    if not event_sources:
        report["degraded"].append("No event csv source found in spec.")
        Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    src = event_sources[0]
    src_path = _find_source_file(base, src["path"])
    if not src_path:
        report["degraded"].append(f"Event source not found: {src['path']}")
        Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    df = load_table(str(src_path))
    popper = PopperGate.check(df)
    report["sources"].append({"type": "event_csv", "path": str(src_path), "popper": popper})

    # 2) dictionary alias map (kolon normalizasyonu rapora)
    if dict_df is not None:
        alias = build_alias_map(list(df.columns), dict_df)
        report["event_schema"] = {"columns": list(df.columns), "alias_map": alias}
    else:
        report["degraded"].append("Metric dictionary missing -> no canonical aliasing.")

    # 3) team reports
    for t in team_names:
        reg = extract_team_metrics(df, t).all()
        report["teams"][t] = [m.as_dict() for m in reg]

    # 4) inventory gate (şimdilik sadece rapora koyuyoruz; corr engine sonra)
    if inv_df is not None:
        report["corr_allowed_sheets"] = allowed_sheets_for_corr(inv_df, max_corr_pairs=15000)
    else:
        report["degraded"].append("Data inventory missing -> no cost gating for correlations.")

    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
