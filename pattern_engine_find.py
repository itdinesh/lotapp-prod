"""
pattern_engine_find.py
TRUE HISTORICAL PREDICTION (Corrected)
Each row's next1, next2, next3 are predicted using rules updated step-by-step.
"""

from typing import List, Dict, Any
from collections import defaultdict, Counter


# ----------------------------------------------------------
# CLEAN DIGITS
# ----------------------------------------------------------

def _clean_digits_str(s: str) -> str:
    """Return clean 5-digit string."""
    s = str(s)
    digits = ''.join(ch for ch in s if ch.isdigit())
    if digits == "":
        digits = "00000"
    return digits.zfill(5)[-5:]


# ----------------------------------------------------------
# TRAIN RULES FROM A SEQUENCE
# ----------------------------------------------------------

def train_rules(cleaned_seq: list):
    """Build full-map & pos-map rules from a cleaned list."""

    full_map_counts = defaultdict(Counter)
    pos_map_counts = {i: defaultdict(Counter) for i in range(1, 6)}

    # Build counters
    for i in range(1, len(cleaned_seq)):
        prev = cleaned_seq[i - 1]
        cur = cleaned_seq[i]

        full_map_counts[prev][cur] += 1

        for pos in range(5):
            # SAFETY CHECKS
            if pos >= len(prev) or pos >= len(cur):
                continue

            if not prev[pos].isdigit() or not cur[pos].isdigit():
                continue

            pd = int(prev[pos])
            cd = int(cur[pos])
            pos_map_counts[pos + 1][pd][cd] += 1


    # Extract full-map most common transitions
    full_map = {}
    for prev, cnt in full_map_counts.items():
        nxt, _ = cnt.most_common(1)[0]
        full_map[prev] = nxt

    # Extract pos-map transitions
    pos_map = {i: {} for i in range(1, 6)}
    for pos in range(1, 6):
        for pd, cnt in pos_map_counts[pos].items():
            nxt, _ = cnt.most_common(1)[0]
            pos_map[pos][pd] = nxt

    return full_map, pos_map


# ----------------------------------------------------------
# EMPIRICAL PREDICTOR
# ----------------------------------------------------------

def empirical_predict(prev_full: str, full_map, pos_map):
    """
    Weighted Hybrid Predictor
    Combines:
    - Full-map (strongest weight)
    - Digit-map (fallback)
    - Mirror rule (lottery logic)
    - Trend rule (+1 digit trend)
    """

    prev_full = _clean_digits_str(prev_full)

    # ----------------------------------------------------
    # 1) FULL-MAP PREDICTION (strongest, weight 5)
    # ----------------------------------------------------
    if prev_full in full_map:
        full_map_pred = full_map[prev_full]
    else:
        full_map_pred = None

    # ----------------------------------------------------
    # 2) DIGIT-MAP PREDICTION (weight 3)
    # ----------------------------------------------------
    digit_pred = []
    for pos in range(1, 6):
        digit = int(prev_full[pos - 1])
        if digit in pos_map[pos]:
            digit_pred.append(str(pos_map[pos][digit]))
        else:
            digit_pred.append(str(digit))
    digit_pred = "".join(digit_pred)

    # ----------------------------------------------------
    # 3) MIRROR RULE PREDICTION (weight 1)
    #    last digit → (digit + 5) % 10
    # ----------------------------------------------------
    last_digit = int(prev_full[-1])
    mirror_digit = (last_digit + 5) % 10
    mirror_pred = prev_full[:-1] + str(mirror_digit)

    # ----------------------------------------------------
    # 4) TREND RULE PREDICTION (weight 1)
    #    last digit → (digit + 1) % 10
    # ----------------------------------------------------
    trend_digit = (last_digit + 1) % 10
    trend_pred = prev_full[:-1] + str(trend_digit)

    # ----------------------------------------------------
    # 5) Weighted Voting System
    # ----------------------------------------------------
    votes = Counter()

    if full_map_pred:
        votes[full_map_pred] += 5

    votes[digit_pred] += 3
    votes[mirror_pred] += 1
    votes[trend_pred] += 1

    # Return highest-weighted prediction
    best_prediction = votes.most_common(1)[0][0]
    return best_prediction

def safe_get(row, key, default=None):
    try:
        return row[key]      # sqlite3.Row or dict
    except Exception:
        return default


# ----------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------

def analyze_patterns(historyData: List[Any]) -> Dict[str, Any]:

    cleaned = []
    times = []

    # Step 1 — clean winners + capture time_col (SAFE)
    for row in historyData:
        raw = safe_get(row, "winner", "")
        time_val = safe_get(row, "time_col")

        cleaned.append(_clean_digits_str(raw))
        times.append(time_val)

    pattern_rows = []

    # Step 2 — generate predictions row-by-row
    for i, prev in enumerate(cleaned):

        slice1 = cleaned[: i + 1]
        full1, pos1 = train_rules(slice1)
        next1 = empirical_predict(prev, full1, pos1)

        slice2 = slice1 + [next1]
        full2, pos2 = train_rules(slice2)
        next2 = empirical_predict(next1, full2, pos2)

        slice3 = slice2 + [next2]
        full3, pos3 = train_rules(slice3)
        next3 = empirical_predict(next2, full3, pos3)

        digits = [int(d) for d in next1]
        rev = digits[::-1]

        pattern_rows.append({
            "Pattern": "Empirical-Historical",
            "index": i,
            "winner": prev,
            "time_col": times[i],   # ✅ works now
            "next1": next1,
            "next2": next2,
            "next3": next3,
            "aaa": rev[4] if len(rev) > 4 else None,
            "aa":  rev[3] if len(rev) > 3 else None,
            "a":   rev[2] if len(rev) > 2 else None,
            "b":   rev[1] if len(rev) > 1 else None,
            "c":   rev[0] if len(rev) > 0 else None,
        })

    rows_all = pattern_rows[-10:] if len(pattern_rows) >= 10 else pattern_rows
    return {"rows": rows_all, "rules": {}}
