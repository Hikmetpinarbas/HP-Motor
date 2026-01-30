from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from hp_motor.ingestion.loaders import load_events
from hp_motor.ingestion.normalizers import normalize_events
from hp_motor.segmentation.set_piece_state import tag_set_piece_state
from hp_motor.segmentation.phase_tagger import tag_phases
from hp_motor.metrics.factory import compute_raw_metrics
from hp_motor.context.engine import apply_context
from hp_motor.report.generator import generate_report
from hp_motor.report.schema import validate_report

REQUIRED = ["match_id","team_id","period","minute","second","event_type"]

def _popper(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {"status":"BLOCKED","hard_errors":["events_table_missing_or_empty"],"flags":[]}
    # SOT hard block
    for e in events[:50]:
        sot = str(e.get("sot","")).upper().strip()
        if sot in {"ERROR","BROKEN"}:
            return {"status":"BLOCKED","hard_errors":[f"sot_hard_block:{sot}"],"flags":[]}
    missing = [c for c in REQUIRED if all(c not in e for e in events)]
    if missing:
        return {"status":"BLOCKED","hard_errors":[f"missing_required_columns:{missing}"],"flags":[]}
    return {"status":"OK","hard_errors":[],"flags":[]}

def run_pipeline(events_path: Path, vendor: str = "generic") -> Dict[str, Any]:
    raw = load_events(events_path)
    pop = _popper(raw)
    if pop["status"] == "BLOCKED":
        rep = generate_report(popper_status="BLOCKED", hard_errors=pop["hard_errors"], flags=[],
                              events_summary={"n_events": len(raw) if raw else 0},
                              metrics_raw={}, metrics_adjusted={}, context_flags=[])
        validate_report(rep)
        return rep

    events = normalize_events(raw, vendor=vendor)
    events = tag_set_piece_state(events)
    events = tag_phases(events)

    metrics_raw = compute_raw_metrics(events)
    metrics_adj, ctx_flags = apply_context(metrics_raw)

    rep = generate_report(popper_status="OK", hard_errors=[], flags=[],
                          events_summary={"n_events": len(events)},
                          metrics_raw=metrics_raw, metrics_adjusted=metrics_adj, context_flags=ctx_flags)
    validate_report(rep)
    return rep
