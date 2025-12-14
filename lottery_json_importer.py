import json
from datetime import datetime
from database_manager import DatabaseManager


# ---------------------------------------------------------
# DIGIT EXTRACTION LOGIC (SAFE)
# ---------------------------------------------------------
def extract_digits(number: str):
    number = number.strip()

    # Ensure 5-digit number
    if len(number) != 6 or not number.isdigit():
        print("❌ Invalid number format:", number)
        return None

    AAA_first = number[1]
    AA_second = number[2]
    A_third = number[3]
    B_fourth = number[4]
    C_last = number[5]

    return {
        "aaa_first": AAA_first,
        "aa_second": AA_second,
        "a_third": A_third,
        "b_fourth": B_fourth,
        "c_last": C_last,
        "last4": number[2:],          # 1620
        "last3": number[3:],          # 620
        "ab": A_third + B_fourth,     # 62
        "bc": B_fourth + C_last,      # 20
        "ac": A_third + C_last        # 60
    }


# ---------------------------------------------------------
# DATE PARSER (AUTO-FIX FORMAT)
# ---------------------------------------------------------
def parse_date(date_str: str):
    date_str = date_str.replace(",", "").strip()

    try:
        return datetime.strptime(date_str, "%d %B %Y")
    except Exception as e:
        print("❌ Date parse failed:", date_str, "Error:", e)
        return None


# ---------------------------------------------------------
# JSON PARSER
# ---------------------------------------------------------
def parse_lottery_json(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    results = []

    for item in data:
        winner_raw = item["winner"]

        # Expected: "89J 01620" or "89J    01620"
        parts = winner_raw.split()

        if len(parts) == 2:
            prefix, number = parts
        else:
            # Attempt auto-fix if format wrong
            number = "".join(filter(str.isdigit, winner_raw))
            prefix = "".join(filter(str.isalpha, winner_raw))

        digits = extract_digits(number)
        if digits is None:
            continue  # skip bad entry

        dt = parse_date(item["date"])
        if dt is None:
            continue

        results.append({
            "sort_key": dt,
            "lottery_name": item["lottery_name"],
            "date": item["date"],
            "time": item["time"],
            "winner": winner_raw,

            # extracted digits
            **digits
        })

    # SORT results by date
    results.sort(key=lambda x: x["sort_key"])
    return results


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    db = DatabaseManager("lottery.db")

    rows = parse_lottery_json("lottery.json")

    db.store_lottery_data(rows)

    print("🎉 JSON Lottery Import Completed Successfully!")
