from __future__ import annotations
from typing import Any, Dict, List
from hp_motor.config_reader import read_spec

def compute_raw_metrics(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    spec = read_spec()
    prog_dx = float(spec.get("hp_motor", {}).get("progressive_pass_dx_threshold", 15.0))

    pass_count = 0
    prog_pass = 0
    shot = 0
    turnover = 0
    have_xy = True

    for e in events:
        et = str(e.get("event_type","")).lower()

        if et == "pass":
            pass_count += 1
            if "start_x" in e and "end_x" in e:
                try:
                    dx = float(e["end_x"]) - float(e["start_x"])
                    if dx >= prog_dx: prog_pass += 1
                except Exception:
                    have_xy = False
            else:
                have_xy = False

        if "shot" in et:
            shot += 1

        if et in {"turnover","dispossessed"}:
            turnover += 1
        if et == "pass" and str(e.get("outcome","")).lower() in {"fail","failed","incomplete","lost"}:
            turnover += 1
        if et in {"carry","dribble"} and str(e.get("outcome","")).lower() in {"fail","failed","lost"}:
            turnover += 1

    return {
        "meta": {"thresholds": {"progressive_pass_dx": prog_dx}, "counts": {"events": len(events)}},
        "metrics": {
            "M_PASS_COUNT": {"value": pass_count, "status": "OK"},
            "M_PROG_PASS_COUNT": {"value": prog_pass, "status": "OK" if have_xy else "DEGRADED"},
            "M_SHOT_COUNT": {"value": shot, "status": "OK"},
            "M_TURNOVER_COUNT": {"value": turnover, "status": "OK" if turnover > 0 else "DEGRADED"}
        }
    }
