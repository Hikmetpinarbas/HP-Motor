from __future__ import annotations
from typing import Any, Dict, List

def tag_phases(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for e in events:
        if e.get("phase"):
            e["phase"] = str(e["phase"]).strip().upper()
            continue
        et = str(e.get("event_type","")).lower()
        if any(k in et for k in ["recovery","interception","counter","transition"]):
            ph = "P6_TRANSITION"
        elif any(k in et for k in ["press","pressure"]):
            ph = "P5_DEF_PRESS"
        elif any(k in et for k in ["block","clearance"]):
            ph = "P4_DEF_BLOCK"
        elif any(k in et for k in ["shot","cross","key_pass","chance"]):
            ph = "P3_ATTACK_FINAL"
        elif any(k in et for k in ["carry","dribble","progressive","through"]):
            ph = "P2_ATTACK_PROG"
        else:
            ph = "P1_ATTACK_BUILD"
        e["phase"] = ph
    return events
