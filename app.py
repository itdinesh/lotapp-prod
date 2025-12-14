from flask import Flask, render_template, request
from database_manager import DatabaseManager
from collections import Counter
from pattern_engine import analyze_history_patterns
from pattern_engine_cust import PatternEngine
import requests

app = Flask(__name__)
db = DatabaseManager("lottery.db")




# -------------------------------------------------------
# DETECT TREND
# -------------------------------------------------------
def detect_trend(values):
    nums = []
    for v in values:
        try:
            nums.append(int(v))
        except:
            continue

    if len(nums) < 3:
        return "Not enough data"

    inc = sum(1 for i in range(1, len(nums)) if nums[i] > nums[i - 1])
    dec = sum(1 for i in range(1, len(nums)) if nums[i] < nums[i - 1])

    if inc > dec:
        return "Increasing"
    elif dec > inc:
        return "Decreasing"
    else:
        return "Mixed"


# -------------------------------------------------------
# FOLLOW FIXED SEQUENCE
# -------------------------------------------------------
def follow_sequence(full_list, base_seq):
    results = []
    L = len(base_seq)

    base_values = [x["value"] for x in base_seq]

    for i in range(len(full_list) - L):
        window = full_list[i:i + L]
        window_values = [x["value"] for x in window]

        if window_values == base_values:
            next_item = full_list[i + L]

            results.append({
                "matched": base_values[:],
                "next": {
                    "value": next_item["value"],
                    "id": next_item["id"]   # 👈 related ID
                }
            })

    return results


# def follow_sequence(full_list, base_seq):
#     results = []
#     L = len(base_seq)

#     for i in range(len(full_list) - L + 1):
#         if full_list[i:i + L] == base_seq:
#             before = full_list[max(0, i-L):i]
#             matched = base_seq[:]
#             after = full_list[i + L:]

#             results.append({
#                 "before": before,
#                 "matched": matched,
#                 "after": after
#             })

#     return results

# -------------------------------------------------------
# BUILD LEVELS
# -------------------------------------------------------
def build_levels(values):
    res = {}

    if len(values) >= 4:
        b = values[-4:]
        res["last4"] = {"base": b, "matches": follow_sequence(values, b)}

    if len(values) >= 3:
        b = values[-3:]
        res["last3"] = {"base": b, "matches": follow_sequence(values, b)}

    if len(values) >= 2:
        b = values[-2:]
        res["last2"] = {"base": b, "matches": follow_sequence(values, b)}

    if len(values) >= 1:
        b = values[-1:]
        res["last1"] = {"base": b, "matches": follow_sequence(values, b)}

    return res



# -------------------------------------------------------
# PREDICTIONS
# -------------------------------------------------------
def build_predictions(time_filter):
    rows = db.get_all_history(time_filter)
    if not rows:
        return {}

    fields = {
        "4digit": "last4",
        "3digit": "last3",
        "ab": "last2_ab",
        "bc": "last2_bc",
        "ac": "last2_ac",
        "a": "a_third",
        "b": "b_fourth",
        "c": "c_last"
    }

    # store dicts instead of plain values
    sequences = {k: [] for k in fields}

    for r in rows:
        for key, col in fields.items():
            if r[col]:
                sequences[key].append({
                    "value": r[col],
                    "id": r["id"]          # 👈 important
                })

    predictions = {key: build_levels(seq) for key, seq in sequences.items()}
    return predictions



# -------------------------------------------------------
# MERGED HISTORY FUNCTION (USE THIS ONLY)
# -------------------------------------------------------
def get_history(time_filter=None):
    rows = db.get_all_history(time_filter)

    history = {
        "date_col": [],
        "time_col": [],
        "Winner": [],
        "LAST4": [],
        "LAST3": [],
        "AB": [],
        "BC": [],
        "AC": [],
        "A": [],
        "B": [],
        "C": []
    }

    for r in rows:
        if r["date_col"]:
            history["date_col"].append(r["date_col"])
        if r["time_col"]:
            history["time_col"].append(r["time_col"])
        if r["Winner"]:
            history["Winner"].append(r["Winner"])
        if r["last4"]:
            history["LAST4"].append(r["last4"])
        if r["last3"]:
            history["LAST3"].append(r["last3"])
        if r["last2_ab"]:
            history["AB"].append(r["last2_ab"])
        if r["last2_bc"]:
            history["BC"].append(r["last2_bc"])
        if r["last2_ac"]:
            history["AC"].append(r["last2_ac"])
        if r["a_third"]:
            history["A"].append(r["a_third"])
        if r["b_fourth"]:
            history["B"].append(r["b_fourth"])
        if r["c_last"]:
            history["C"].append(r["c_last"])

    return history


# -------------------------------------------------------
# AI SUMMARY BASED ON LAST4 ONLY
# -------------------------------------------------------
def generate_historical_summary(history):
    seq_list = history.get("LAST4", [])
    summary = {}

    if not seq_list:
        return summary

    freq = Counter(seq_list).most_common()
    values_only = [v for v, _ in freq]

    numeric_vals = [int(v) for v in seq_list if v.isdigit()]
    low = min(numeric_vals) if numeric_vals else None
    high = max(numeric_vals) if numeric_vals else None

    trend = detect_trend(seq_list)

    summary["4digit"] = {
        "total": len(seq_list),
        "unique": len(set(seq_list)),
        "most_common": values_only[:5],
        "range_low": low,
        "range_high": high,
        "trend": trend
    }

    return summary


# -------------------------------------------------------
# FINAL PREDICTION (SUMMARY-BASED)
# -------------------------------------------------------
def build_final_prediction(summary):
    final4 = summary.get("4digit", {}).get("most_common", [])
    return {"final4": final4, "top_all": final4[:]}


# -------------------------------------------------------
# AI PROMPT (OPTION 4 – A,B,C MATRIX FOR LAST3)
# -------------------------------------------------------
MAX_AI_HISTORY = 120

def build_ai_prompt(history):
    last3_values = history.get("LAST3", [])
    last3_values = last3_values[-MAX_AI_HISTORY:]  # preserve order

    prompt = (
        "You are a deterministic 3-digit sequence analyzer.\n"
        "NO randomness. Use strict rules only.\n\n"

        "TASK:\n"
        "1. Split each LAST3 value into A,B,C columns.\n"
        "2. Compute modulo-10 transitions for each column.\n"
        "3. Detect the strongest pattern using the following priority rules:\n"
        "      Rule 1: Repeating diff cycle\n"
        "      Rule 2: Mirror pattern (next = 9 - previous)\n"
        "      Rule 3: Digit frequency preference\n"
        "      Rule 4: Recent-trend dominance (last 3 transitions)\n"
        "      Rule 5: Tie-break → choose pattern generating the higher digit.\n"
        "\n"
        "4. Use the pattern to compute A_next, B_next, C_next.\n"
        "5. Output ONLY the tables + numeric reasoning.\n\n"

        "STRICT OUTPUT FORMAT:\n"
        "1) Table of split digits\n"
        "2) Transition differences (A,B,C)\n"
        "3) Pattern chosen + reason (1 line)\n"
        "4) A_next, B_next, C_next\n"
        "5) NEXT = ABC\n\n"

        "HISTORICAL LAST3 VALUES (exact order):\n"
        + ", ".join(str(v) for v in last3_values) +
        "\n\n"
        "Now process the data.\n"
    )

    return prompt



# -------------------------------------------------------
# CALL GROQ AI
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_groq_ai(prompt):
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Respond ALWAYS in clean table format"},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.1-8b-instant",
            # model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"AI Error: {e}"


# -------------------------------------------------------
# NORMALIZE LAST4 LIST
# -------------------------------------------------------
def normalize_last4(values, window=60):
    """
    Take last `window` LAST4 values, ensure they are 4-digit numeric strings.
    """
    tail = values[-window:]
    norm = []
    for v in tail:
        if not v:
            continue
        digits = "".join(ch for ch in str(v) if ch.isdigit())
        if not digits:
            continue
        digits = digits[-4:].zfill(4)
        norm.append(digits)
    return norm


# -------------------------------------------------------
# LAST4 PREDICTION USING SIMPLE MATRIX LOGIC (RULE B)
# -------------------------------------------------------
def predict_next_last4(history_last4):
    """
    Use LAST4 values, treat as ABCD digits, and apply:
    - raw differences per column
    - next digit = last_digit + abs(last_raw_diff) (Rule B)
    """
    data = normalize_last4(history_last4, window=60)
    if len(data) < 2:
        return ""

    A = [int(v[0]) for v in data]
    B = [int(v[1]) for v in data]
    C = [int(v[2]) for v in data]
    D = [int(v[3]) for v in data]

    def col_diffs(col):
        raw = [col[i] - col[i - 1] for i in range(1, len(col))]
        # mod = [(col[i] - col[i - 1]) % 10 for i in range(1, len(col))]
        return raw

    A_raw = col_diffs(A)
    B_raw = col_diffs(B)
    C_raw = col_diffs(C)
    D_raw = col_diffs(D)

    def next_digit(last_digit, raw_seq):
        step = abs(raw_seq[-1])
        return (last_digit + step) % 10

    A_next = next_digit(A[-1], A_raw)
    B_next = next_digit(B[-1], B_raw)
    C_next = next_digit(C[-1], C_raw)
    D_next = next_digit(D[-1], D_raw)

    return f"{A_next}{B_next}{C_next}{D_next}"

def build_history_dict(rows):
    if not rows:
        return {}

    history = {
        "LAST4": [],
        "LAST3": [],
        "AB": [],
        "BC": [],
        "AC": [],
        "A": [],
        "B": [],
        "C": []
    }

    for row in rows:

        # 4-digit
        if "last4" in row.keys() and row["last4"]:
            history["LAST4"].append(str(row["last4"]))

        # 3-digit
        if "last3" in row.keys() and row["last3"]:
            history["LAST3"].append(str(row["last3"]))

        # AB / BC / AC (2-digit pairs)
        if "last2_ab" in row.keys() and row["last2_ab"]:
            history["AB"].append(str(row["last2_ab"]))

        if "last2_bc" in row.keys() and row["last2_bc"]:
            history["BC"].append(str(row["last2_bc"]))

        if "last2_ac" in row.keys() and row["last2_ac"]:
            history["AC"].append(str(row["last2_ac"]))

        # A, B, C (single digits)
        if "a_third" in row.keys() and row["a_third"]:
            history["A"].append(str(row["a_third"]))

        if "b_fourth" in row.keys() and row["b_fourth"]:
            history["B"].append(str(row["b_fourth"]))

        if "c_last" in row.keys() and row["c_last"]:
            history["C"].append(str(row["c_last"]))

    return history

# -------------------------------------------------------
# MAIN PAGE
# -------------------------------------------------------
@app.route("/")
def index():

    selected_lottery = request.args.get("lottery_name", "")
    selected_date = request.args.get("date_col", "")
    selected_times = request.args.getlist("time_col")

    page = int(request.args.get("page", 1))

    filters = db.get_lottery_filters()
    
    rows, total = db.get_lottery_rows(
        selected_lottery or None,
        selected_date or None,
        selected_times or None,
        page
    )

    total_pages = max((total + 2) // 3, 1)

    history = get_history(selected_times or None)

    ai_summary = generate_historical_summary(history)
    final_prediction = build_final_prediction(ai_summary)

    # AI (Groq) – A,B,C matrix on LAST3
    prompt = build_ai_prompt(history)
    ai_output = ask_groq_ai(prompt)

    rowsHis = db.get_all_history(selected_times or None)
    historyData = build_history_dict(rowsHis)
    pattern_results = analyze_history_patterns(historyData)

    predictions = build_predictions(selected_times or None)

    from pattern_engine_find import analyze_patterns

    historyDataFind = db.get_all_history(selected_times or None)

  # safe printing for both old and new output shapes
    pattern_results_find_full = analyze_patterns(historyDataFind)




    # ✅ Your requested change: use LAST4 for numeric prediction
    correct_last3_prediction = predict_next_last4(history["LAST4"])

    last4_1pm = db.get_last4("1 PM")
    last4_6pm = db.get_last4("6 PM")
    last4_8pm = db.get_last4("8 PM")
    last4_combined = db.get_last4("COMBINED")
    engine = PatternEngine()
    

    return render_template(
        "index.html",
        filters=filters,
        rows=rows,
        total_pages=total_pages,
        page=page,
        selected_lottery=selected_lottery,
        selected_date=selected_date,
        selected_time=selected_times,
        predictions=predictions,
        ai_summary=ai_summary,
        final_prediction=final_prediction,
        last4_1pm=last4_1pm,
        last4_6pm=last4_6pm,
        last4_8pm=last4_8pm,
        last4_combined=last4_combined,
        ai_output=ai_output,
        correct_last3_prediction=correct_last3_prediction,
        pattern_results=pattern_results, 
        pattern_results_find=pattern_results_find_full,
    )


# -------------------------------------------------------
# SAVE RECORD
# -------------------------------------------------------
import re
from flask import request
@app.route("/save_record", methods=["POST"])
def save_record():

    raw_winner = request.form.get("winner", "").strip()

    # Extract last numeric group (handles "48B 11197" or "11197")
    nums = re.findall(r"\d+", raw_winner.replace(" ", ""))
    if nums:
        d = nums[-1]
    else:
        d = ""  # fallback

    # Individual digit fields (safe checks)
    aaa_first = d[0] if len(d) >= 1 else ""
    aa_second = d[1] if len(d) >= 2 else ""       # second digit only (changed)
    a_third = d[2] if len(d) >= 3 else ""
    b_fourth = d[3] if len(d) >= 4 else ""
    c_last = d[-1] if len(d) >= 1 else ""

    # Slices
    last4 = d[-4:] if len(d) >= 4 else d
    last3 = d[-3:] if len(d) >= 3 else d

    # Custom pairs per your correction
    ab = (d[2] + d[3]) if len(d) >= 4 else ""      # 3rd + 4th digits
    bc = (d[3] + d[-1]) if len(d) >= 4 else ""     # 4th + last digit
    ac = (d[2] + d[-1]) if len(d) >= 3 else ""     # 3rd + last digit

    record = {
        "lottery_name": request.form.get("lottery_name"),
        "date": request.form.get("date_col"),
        "time": request.form.get("time_col"),
        "winner": d,   # store cleaned digits

        "aaa_first": aaa_first,
        "aa_second": aa_second,
        "a_third": a_third,
        "b_fourth": b_fourth,
        "c_last": c_last,

        "last4": last4,
        "last3": last3,
        "ab": ab,
        "bc": bc,
        "ac": ac
    }

    db.store_lottery_data([record])
    return "<h3>Record Saved Successfully! <a href='/'>Go Back</a></h3>"

if __name__ == "__main__":
    # app.run(debug=True)    
    app.run(host="0.0.0.0", port=10000)
