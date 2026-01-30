from __future__ import annotations
from typing import Any, Dict, List

SET_PIECE_KEYWORDS = {"corner":"corner","free_kick":"free_kick","throw_in":"throw_in","penalty":"penalty","kick_off":"kick_off"}

def tag_set_piece_state(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for e in events:
        if e.get("set_piece_state"):
            e["set_piece_state"] = str(e["set_piece_state"]).strip().lower()
            continue
        et = str(e.get("event_type","")).lower()
        sp = "open_play"
        for k,v in SET_PIECE_KEYWORDS.items():
            if k in et:
                sp = v
                break
        e["set_piece_state"] = sp
    return events
