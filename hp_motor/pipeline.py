from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from hp_motor.ingestion.loaders import load_events
from hp_motor.ingestion.normalizers import normalize_events
from hp_motor.library import library_health
from hp_motor.segmentation.set_piece_state import tag_set_piece_state
from hp_motor.segmentation.phase_tagger import tag_phases
from hp_motor.metrics.factory import compute_raw_metrics
from hp_motor.context.engine import apply_context
from hp_motor.report.generator import generate_report
from hp_motor.report.schema import validate_report


REQUIRED_EVENT_COLUMNS = [
    "match_id",
    "team_id",
    "period",
    "minute",
    "second",
    "event_type",
]


def _popper(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Popper hard block only:
      - events missing/empty
      - required columns missing
      - SOT=ERROR/BROKEN
    Otherwise:
      - OK or DEGRADED with flags
    """
    if events is None or len(events) == 0:
        return {"status": "BLOCKED", "hard_errors": ["events_table_missing_or_empty"], "flags": []}

    # SOT hard block (first N events is enough)
    for e in events[:50]:
        sot = str(e.get("sot", "")).upper().strip()
        if sot in {"ERROR", "BROKEN"}:
            return {"status": "BLOCKED", "hard_errors": [f"sot_hard_block:{sot}"], "flags": []}

    missing_required = [c for c in REQUIRED_EVENT_COLUMNS if all(c not in ev for ev in events)]
    if missing_required:
        return {"status": "BLOCKED", "hard_errors": [f"missing_required_columns:{missing_required}"], "flags": []}

    # Soft flags (never block)
    flags: List[str] = []
    soft_cols = ["possession_id", "sequence_id", "start_x", "start_y", "end_x", "end_y", "outcome"]
    for c in soft_cols:
        if all(c not in ev for ev in events):
            flags.append(f"missing_soft_column:{c}")

    status = "OK" if not flags else "DEGRADED"
    return {"status": status, "hard_errors": [], "flags": flags}


def run_pipeline(events_path: Path, vendor: str = "generic") -> Dict[str, Any]:
    raw_events = load_events(events_path)
    pop = _popper(raw_events)

    lib_h = library_health()

    if pop["status"] == "BLOCKED":
        report = generate_report(
            popper_status="BLOCKED",
            hard_errors=pop["hard_errors"],
            flags=[],
            events_summary={"n_events": len(raw_events) if raw_events else 0},
            metrics_raw={"meta": {"library_health": lib_h.__dict__}, "metrics": {}},
            metrics_adjusted={},
            context_flags=["library:" + lib_h.status] + lib_h.flags,
        )
        validate_report(report)
        return report

    # Normalize
    events = normalize_events(raw_events, vendor=vendor)

    # Tagging (lite but deterministic)
    events = tag_set_piece_state(events)
    events = tag_phases(events)

    # Raw metrics
    metrics_raw = compute_raw_metrics(events)
    # attach library info into meta
    metrics_raw.setdefault("meta", {})
    metrics_raw["meta"]["library_health"] = lib_h.__dict__

    # Context (identity v0 + flags)
    metrics_adjusted, ctx_flags = apply_context(metrics_raw)

    context_flags = ["library:" + lib_h.status] + lib_h.flags + ctx_flags

    report = generate_report(
        popper_status=pop["status"],
        hard_errors=[],
        flags=pop["flags"],
        events_summary={"n_events": len(events)},
        metrics_raw=metrics_raw,
        metrics_adjusted=metrics_adjusted,
        context_flags=context_flags,
    )
    validate_report(report)
    return report
