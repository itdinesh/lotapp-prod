# ================================================================
# NAGALAND LOTTERY – STABLE PATTERN ENGINE (FULL UPDATED FILE)
# Includes:
# ✔ Full pattern return (Cycle, Mirror, Drift, Freeze, Reset, Custom, Fallback)
# ✔ Combined prediction list
# ✔ Deep next-series analysis (FIXED STEP-1 BUG)
# ✔ All patterns always included with None when absent
# ================================================================

from collections import Counter


# ============================================================
# NORMALIZE TO DIGITS
# ============================================================
def normalize(values, digits):
    cleaned = []
    for v in values:
        s = "".join(c for c in str(v) if c.isdigit())
        if len(s) < digits:
            continue
        cleaned.append([int(x) for x in s[-digits:]])
    return cleaned


# ============================================================
# DIGIT-WISE RAW & MOD
# ============================================================
def compute_transitions(col):
    raw, mod = [], []
    for i in range(1, len(col)):
        diff = col[i] - col[i - 1]
        raw.append(diff)
        mod.append(diff % 10)
    return raw, mod


# ============================================================
# FOLLOW FIXED SEQUENCE
# ============================================================
def follow_fixed_sequence(seq, digits):
    if len(seq) < digits + 1:
        return None, None, None

    base = seq[-digits:]
    L = digits

    for i in range(len(seq) - L - 1):
        if seq[i:i + L] == base:
            full_before = seq[:i + L]
            before = full_before[-5:]     # last 5 only

            full_after = seq[i + L:]
            after = full_after[:5]        # first 5 only

            return before, base, after

    return None, None, None


# ============================================================
# PATTERN DETECTION
# ============================================================
def detect_cycle(mod):
    n = len(mod)
    if n < 6:
        return None
    for L in range(2, min(8, n // 2 + 1)):
        if mod[-L:] == mod[-2 * L:-L]:
            return mod[-L:]
    return None


def detect_mirror(mod):
    if len(mod) < 4:
        return None
    for i in range(len(mod) - 3):
        a, b, c, d = mod[i:i + 4]
        if (a % 10) == ((-b) % 10) and (c % 10) == ((-d) % 10):
            return a
    return None


def detect_drift(col):
    if len(col) < 3:
        return None

    ups = sum(col[i] > col[i - 1] for i in range(1, len(col)))
    downs = sum(col[i] < col[i - 1] for i in range(1, len(col)))
    total = len(col) - 1

    if ups >= total * 0.65:
        return "UP"
    if downs >= total * 0.65:
        return "DOWN"
    return None


def detect_freeze(col):
    streak = 1
    for i in range(1, len(col)):
        if col[i] == col[i - 1]:
            streak += 1
            if streak >= 4:
                return col[i]
        else:
            streak = 1
    return None


def detect_reset(mod):
    return sum(x >= 7 for x in mod) >= 3


# ============================================================
# DECISION ENGINE
# ============================================================
def decide_next(col, raw, mod, col_name, digits):
    seq = col
    last = seq[-1]

    before, base, after = follow_fixed_sequence(seq, digits)

    results = {
        "before": before,
        "base": base,
        "after": after,
        "cycle": None,
        "mirror": None,
        "drift": None,
        "freeze": None,
        "reset": None,
        "fallback": None,
        "custom": None
    }

    # FOLLOW FIXED SEQUENCE HAS TOP PRIORITY
    if base is not None:
        results["final"] = after[0] if after else last
        return results

    cycle = detect_cycle(mod)
    mirror = detect_mirror(mod)
    drift = detect_drift(seq)
    freeze = detect_freeze(seq)
    reset = detect_reset(mod)

    results["cycle"] = (last + cycle[0]) % 10 if cycle else None
    results["mirror"] = (last + mirror) % 10 if mirror is not None else None

    if drift == "UP":
        results["drift"] = (last + 1) % 10
    elif drift == "DOWN":
        results["drift"] = (last - 1) % 10

    results["freeze"] = freeze
    results["reset"] = (last + Counter(mod).most_common(1)[0][0]) % 10 if reset else None
    results["fallback"] = (last + mod[-1]) % 10 if mod else None
    results["custom"] = None

    for key in ["cycle", "mirror", "drift", "freeze", "reset", "fallback"]:
        if results[key] is not None:
            results["final"] = results[key]
            return results

    results["final"] = last
    return results


# ============================================================
# MULTI-STEP FORECAST
# ============================================================
def predict_series(values, digits, steps=5):
    seq = list(values)
    out = []

    for _ in range(steps):
        norm = normalize(seq, digits)
        if len(norm) < 3:
            break

        cols = list(zip(*norm))
        next_digits = []

        for idx, col in enumerate(cols):
            col = list(col)
            raw, mod = compute_transitions(col)

            col_name = (
                ["A", "B", "C"][idx] if digits == 3 else
                ["A", "B"][idx] if digits == 2 else
                str(idx)
            )

            result = decide_next(col, raw, mod, col_name, digits)
            next_digits.append(result["final"])

        next_val = "".join(str(x) for x in next_digits)
        out.append(next_val)
        seq.append(next_val)

    return out


# ============================================================
# DEEP ANALYSIS OF NEXT SERIES (🔥 FIXED)
# ============================================================
def analyze_next_series(history_list, digits, next_series):
    analysis_out = []
    seq = list(history_list)

    for step_index, val in enumerate(next_series, start=1):

        # ✅ ANALYZE FIRST — DO NOT APPEND YET
        norm = normalize(seq, digits)
        cols = list(zip(*norm))

        step_analysis = []

        for idx, col in enumerate(cols):
            col = list(col)
            raw, mod = compute_transitions(col)

            col_name = (
                ["A", "B", "C"][idx] if digits == 3 else
                ["A", "B"][idx] if digits == 2 else
                str(idx)
            )

            result = decide_next(col, raw, mod, col_name, digits)

            step_analysis.append({
                "column": col_name,
                "column_data": col,
                "raw": raw,
                "mod": mod,
                "patterns": result,
                "next": result["final"]
            })

        analysis_out.append({
            "step": step_index,
            "value": val,
            "analysis": step_analysis
        })

        # ✅ APPEND AFTER ANALYSIS
        seq.append(val)

    return analysis_out


# ============================================================
# MAIN ENTRY FUNCTION
# ============================================================
def analyze_history_patterns(history):
    output = {}

    categories = {
        "LAST4": 4,
        "LAST3": 3,
        "AB": 2,
        "BC": 2,
        "AC": 2,
        "A": 1,
        "B": 1,
        "C": 1,
    }

    for key, digits in categories.items():
        values = history.get(key, [])
        norm = normalize(values, digits)

        if len(norm) < 3:
            output[key] = {"error": "Not enough history"}
            continue

        cols = list(zip(*norm))
        analysis = []
        next_digits = []

        for idx, col in enumerate(cols):
            col = list(col)
            raw, mod = compute_transitions(col)

            col_name = (
                ["A", "B", "C"][idx] if digits == 3 else
                ["A", "B"][idx] if digits == 2 else
                str(idx)
            )

            result = decide_next(col, raw, mod, col_name, digits)
            analysis.append({
                "column": col_name,
                "column_data": col,
                "raw": raw,
                "mod": mod,
                "patterns": result,
                "next": result["final"]
            })

            next_digits.append(str(result["final"]))

        final_prediction = "".join(next_digits)

        next_series = predict_series(values + [final_prediction], digits, 5)
        combined = [final_prediction] + next_series
        next_series_analysis = analyze_next_series(values + [final_prediction], digits, next_series)

        output[key] = {
            "analysis": analysis,
            "prediction": final_prediction,
            "next_series": next_series,
            "combined_predictions": combined,
            "next_series_analysis": next_series_analysis
        }

    return output
