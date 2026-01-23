import json
from pathlib import Path

CANON_ROOT = Path(__file__).resolve().parent / "canon_data"

def load_canon_metrics():
    """
    Loads HP-Engine style metric specs into memory.
    """
    metrics = {}
    if not CANON_ROOT.exists():
        return metrics

    for spec_file in CANON_ROOT.rglob("*.metric_spec.json"):
        with open(spec_file, "r", encoding="utf-8") as f:
            spec = json.load(f)
            metrics[spec["metric_id"]] = spec

    return metrics