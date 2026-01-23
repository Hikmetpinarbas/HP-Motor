from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd


# -----------------------------
# Cognitive Scanning / Awareness
# -----------------------------

@dataclass
class CognitiveSignals:
    decision_speed_mean_s: Optional[float] = None
    decision_speed_p25_s: Optional[float] = None
    scan_freq_10s: Optional[float] = None  # scans per second in the 10s pre-receive window
    scan_count_10s_mean: Optional[float] = None
    contextual_awareness_score: Optional[float] = None  # 0..1
    notes: Optional[str] = None


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def compute_decision_speed(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    """
    Expects either:
      - columns: t1 (receive time), t2 (release time) in seconds
    Returns: (mean, p25) in seconds
    """
    if df is None or df.empty:
        return None, None

    if "t1" not in df.columns or "t2" not in df.columns:
        return None, None

    t1 = _to_numeric(df["t1"])
    t2 = _to_numeric(df["t2"])
    ds = (t2 - t1).replace([np.inf, -np.inf], np.nan)

    if ds.notna().sum() == 0:
        return None, None

    mean = float(ds.mean())
    p25 = float(ds.quantile(0.25))
    return mean, p25


def compute_scan_frequency_10s(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    """
    Two supported input patterns:

    Pattern A (preferred):
      - scan_count_10s : number of scans in 10s pre-receive window (per event row)
        -> scan_freq_10s = mean(scan_count_10s) / 10

    Pattern B:
      - scan_ts : timestamps of scan events (seconds) AND receive_ts per possession/event
        This is more complex; v1.0 supports only Pattern A robustly.

    Returns: (scan_freq_10s, scan_count_10s_mean)
    """
    if df is None or df.empty:
        return None, None

    if "scan_count_10s" in df.columns:
        sc = _to_numeric(df["scan_count_10s"]).replace([np.inf, -np.inf], np.nan)
        if sc.notna().sum() == 0:
            return None, None
        sc_mean = float(sc.mean())
        scan_freq = sc_mean / 10.0
        return scan_freq, sc_mean

    # Optional light support: scan_count with scan_window_s
    if "scan_count" in df.columns and "scan_window_s" in df.columns:
        sc = _to_numeric(df["scan_count"]).replace([np.inf, -np.inf], np.nan)
        win = _to_numeric(df["scan_window_s"]).replace([np.inf, -np.inf], np.nan)
        valid = sc.notna() & win.notna() & (win > 0)
        if valid.sum() == 0:
            return None, None
        scan_freq = float((sc[valid] / win[valid]).mean())
        sc_mean = float(sc[valid].mean())
        return scan_freq, sc_mean

    return None, None


def score_contextual_awareness(decision_speed_mean_s: Optional[float],
                               scan_freq_10s: Optional[float]) -> Optional[float]:
    """
    Score 0..1 combining:
      - decision speed (elite threshold ~0.6s from your snippet)
      - scan frequency thresholds (your conceptual thresholds: >0.6 high, <0.3 low)

    We keep it deliberately simple & falsifiable:
      - decision component: 1.0 if mean < 0.6s else linearly decreases to 0.5 at 1.2s
      - scan component: clamp(scan_freq_10s / 0.6, 0..1) with low warning below 0.3

    Returns: score or None if both missing.
    """
    if decision_speed_mean_s is None and scan_freq_10s is None:
        return None

    # Decision component
    dec = None
    if decision_speed_mean_s is not None:
        if decision_speed_mean_s <= 0.6:
            dec = 1.0
        elif decision_speed_mean_s >= 1.2:
            dec = 0.5
        else:
            # 0.6 -> 1.0, 1.2 -> 0.5
            dec = 1.0 - (decision_speed_mean_s - 0.6) * (0.5 / 0.6)

    # Scan component
    scn = None
    if scan_freq_10s is not None:
        scn = float(np.clip(scan_freq_10s / 0.6, 0.0, 1.0))

    # Combine (if one missing, use the other)
    if dec is None:
        return scn
    if scn is None:
        return dec

    return float(0.55 * scn + 0.45 * dec)


def extract_cognitive_signals(df: pd.DataFrame) -> CognitiveSignals:
    ds_mean, ds_p25 = compute_decision_speed(df)
    scan_freq, scan_count_mean = compute_scan_frequency_10s(df)
    score = score_contextual_awareness(ds_mean, scan_freq)

    notes = []
    if scan_freq is not None:
        if scan_freq >= 0.6:
            notes.append("Scanning: ileri yönlü karar özgüveni yüksek (>=0.6/s).")
        elif scan_freq <= 0.3:
            notes.append("Scanning: güvenli/geri pas eğilimi riski (<=0.3/s).")
        else:
            notes.append("Scanning: orta bant.")

    if ds_mean is not None:
        if ds_mean < 0.6:
            notes.append("Karar hızı: elit (<0.6s).")
        elif ds_mean > 1.2:
            notes.append("Karar hızı: yavaş (>1.2s).")
        else:
            notes.append("Karar hızı: orta bant.")

    return CognitiveSignals(
        decision_speed_mean_s=ds_mean,
        decision_speed_p25_s=ds_p25,
        scan_freq_10s=scan_freq,
        scan_count_10s_mean=scan_count_mean,
        contextual_awareness_score=score,
        notes=" ".join(notes) if notes else None,
    )


# -----------------------------
# Biomechanics / Orientation
# -----------------------------

@dataclass
class OrientationSignals:
    defender_side_on_score: Optional[float] = None  # 0..1 (higher ~ closer to 45°)
    square_on_rate: Optional[float] = None          # proportion near 90°
    channeling_to_wing_rate: Optional[float] = None # if you have channel direction labels
    notes: Optional[str] = None


def _angle_diff(a: float, b: float) -> float:
    # minimal absolute difference on a circle [0,180] for body orientation
    d = abs(a - b) % 180.0
    return min(d, 180.0 - d)


def extract_orientation_signals(df: pd.DataFrame) -> OrientationSignals:
    """
    Supported columns (any one is enough):
      - defender_body_angle_deg / body_angle_deg / body_angle
        meaning: angle of defender stance vs attacker direction, in degrees (0..180)
    Optional:
      - channel_target in {"wing","center"} for channeling
    """
    if df is None or df.empty:
        return OrientationSignals()

    angle_col = None
    for c in ["defender_body_angle_deg", "body_angle_deg", "body_angle"]:
        if c in df.columns:
            angle_col = c
            break

    if angle_col is None:
        return OrientationSignals(notes="Orientation açı kolonu yok (body_angle*).")

    ang = _to_numeric(df[angle_col]).replace([np.inf, -np.inf], np.nan)
    ang = ang.dropna()
    if ang.empty:
        return OrientationSignals(notes="Orientation açı verisi boş/NaN.")

    # Side-on target ~45°
    diffs_45 = ang.apply(lambda x: _angle_diff(float(x), 45.0))
    side_on = float(np.clip(1.0 - (diffs_45.mean() / 45.0), 0.0, 1.0))

    # Square-on near 90° (within +/- 15°)
    square_on = ang.apply(lambda x: _angle_diff(float(x), 90.0) <= 15.0)
    square_on_rate = float(square_on.mean())

    channeling_rate = None
    if "channel_target" in df.columns:
        ct = df["channel_target"].astype(str).str.lower()
        if (ct == "wing").any() or (ct == "center").any():
            channeling_rate = float((ct == "wing").mean())

    notes = []
    notes.append(f"Side-on (45°) uygunluk skoru: {side_on:.2f}")
    notes.append(f"Square-on (90°) oranı: {square_on_rate:.2f}")

    if square_on_rate > 0.35:
        notes.append("Uyarı: Square-on yüksek; biyomekanik reaksiyon riski artar.")
    if side_on < 0.45:
        notes.append("Uyarı: 45° kapısı zayıf; jockeying/CoM disiplini iyileştirilmeli.")

    if channeling_rate is not None:
        notes.append(f"Channeling→Wing oranı: {channeling_rate:.2f}")

    return OrientationSignals(
        defender_side_on_score=side_on,
        square_on_rate=square_on_rate,
        channeling_to_wing_rate=channeling_rate,
        notes=" ".join(notes),
    )