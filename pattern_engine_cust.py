# pattern_engine.py
# ------------------------------------------------------
#  COMPLETE SPLIT-DIGIT + DIFF + PATTERN ENGINE LOGIC
# ------------------------------------------------------

class PatternEngine:

    def __init__(self):
        pass

    # ------------------------------------------------------
    # 1. SPLIT DIGITS FROM A 3-DIGIT NUMBER
    # ------------------------------------------------------
    def split_digits(self, value):
        v = str(value).zfill(3)
        return int(v[0]), int(v[1]), int(v[2])

    # ------------------------------------------------------
    # 2. BUILD ROW TABLE
    # ------------------------------------------------------
    def build_rows(self, values_list):
        rows = []
        prevA = prevB = prevC = None

        for v in values_list:
            A, B, C = self.split_digits(v)

            if prevA is None:
                diffA = diffB = diffC = None
            else:
                diffA = A - prevA
                diffB = B - prevB
                diffC = C - prevC

            rows.append({
                "value": str(v).zfill(3),
                "A": A,
                "B": B,
                "C": C,
                "diffA": diffA,
                "diffB": diffB,
                "diffC": diffC
            })

            prevA, prevB, prevC = A, B, C

        return rows

    # ------------------------------------------------------
    # RULE 2: MIRROR PATTERN DETECTION
    # ------------------------------------------------------
    def detect_mirror_pattern(self, rows):
        for r in reversed(rows):  # check latest first
            if r["A"] == r["B"] and r["A"] != r["C"]:
                return r["A"]
        return None

    # ------------------------------------------------------
    # RULE 4: CHECK LAST 3 TRENDS
    # ------------------------------------------------------
    def last3_trend(self, rows):
        diffs = [r["diffA"] for r in rows if r["diffA"] is not None]

        if len(diffs) == 0:
            return None

        if len(diffs) == 1:
            return [diffs[0], diffs[0], diffs[0]]

        if len(diffs) == 2:
            return [diffs[0], diffs[1], diffs[1]]

        return diffs[-3:]

    # ------------------------------------------------------
    # ⭐ RULE 1: LAST1 DIGIT PREDICTOR (NEW)
    # ------------------------------------------------------
    def last1_digit_logic(self, rows):
        if len(rows) == 1:
            A = rows[0]["A"]
            B = rows[0]["B"]
            C = rows[0]["C"]

            # simple increment pattern for machine pulse logic
            C_next = (C + 1) % 10
            return f"{A}{B}{C_next}"

        return None

    # ------------------------------------------------------
    # MAIN PATTERN ENGINE
    # ------------------------------------------------------
    def compute_next(self, values_list):
        if not values_list:
            return "000"

        rows = self.build_rows(values_list)

        # -----------------------------
        # RULE 1: LAST1 DIGIT RULE
        # -----------------------------
        last1 = self.last1_digit_logic(rows)
        if last1 is not None:
            return last1

        # -----------------------------
        # RULE 2: MIRROR PATTERN
        # -----------------------------
        mirror_digit = self.detect_mirror_pattern(rows)
        if mirror_digit is not None:
            A_next = mirror_digit
            B_next = mirror_digit - 1 if mirror_digit > 0 else 0
            C_next = 0
            return f"{A_next}{B_next}{C_next}"

        # -----------------------------
        # RULE 4: TREND
        # -----------------------------
        trend = self.last3_trend(rows)
        if trend is not None:
            A_next = trend[-1] % 10
            B_next = trend[-2] % 10
            C_next = trend[-3] % 10
            return f"{A_next}{B_next}{C_next}"

        # -----------------------------
        # FALLBACK
        # -----------------------------
        last = rows[-1]
        return f"{last['A']}{last['B']}{last['C']}"

    # ------------------------------------------------------
    # ⭐ MULTIPLE NEXT VALUES
    # ------------------------------------------------------
    def compute_next_multiple(self, values_list, count=5):
        result_list = []
        current_list = list(values_list)

        for _ in range(count):
            nxt = self.compute_next(current_list)
            result_list.append(nxt)
            current_list.append(nxt)

        return result_list
    
    
    # ------------------------------------------------------
    # MULTIPLE NEXT VALUES FOR SINGLE DIGIT
    # ------------------------------------------------------
    def compute_next_single_digit_multiple(self, digit_list, count=5):
        results = []
        history = digit_list.copy()

        for _ in range(count):
            nxt = self.compute_next_single_digit(history)
            results.append(nxt)
            history.append(str(nxt))

        return results

    
    # def compute_next_single_digit(self, digit_list):
    #     digits = [int(d) for d in digit_list if str(d).isdigit()]

    #     if len(digits) == 0:
    #         return 0

    #     # -------------------------------
    #     # MIRROR RULE
    #     # -------------------------------
    #     if len(digits) >= 2:
    #         if digits[-1] == digits[-2]:
    #             nxt = (digits[-1] - 1) % 10
    #             return nxt

    #     # -------------------------------
    #     # 3-DIGIT TREND RULE (NEW)
    #     # ex: 5, 4, 3 → diffs = -1, -1 → continue trend
    #     # -------------------------------
    #     if len(digits) >= 3:
    #         d1 = digits[-3]
    #         d2 = digits[-2]
    #         d3 = digits[-1]

    #         diff1 = d2 - d1
    #         diff2 = d3 - d2

    #         if diff1 == diff2:
    #             nxt = (d3 + diff2) % 10
    #             return nxt

    #     # -------------------------------
    #     # BASIC TREND RULE (fallback)
    #     # -------------------------------
    #     if len(digits) >= 2:
    #         diff = digits[-1] - digits[-2]
    #         nxt = (digits[-1] + diff) % 10
    #         return nxt

    #     return digits[-1]
  
    def compute_next_single_digit(self, digit_list):
        # ------------------------------------
        # CLEAN INPUT
        # ------------------------------------
        digits = [int(d) for d in digit_list if str(d).isdigit()]

        # ------------------------------------
        # FALLBACK RULE: Only one digit
        # ------------------------------------
        if len(digits) < 2:
            return digits[-1]  # repeat it

        # ------------------------------------
        # MIRROR RULE
        # If last two digits are equal → use mirror-down
        # ------------------------------------
        if digits[-1] == digits[-2]:
            return (digits[-1] - 1) % 10

        # ------------------------------------
        # COMPUTE DIFFS
        # ------------------------------------
        diffs = []
        for i in range(1, len(digits)):
            diffs.append(digits[i] - digits[i - 1])

        # ------------------------------------
        # 3-DIGIT TREND RULE
        # If last 3 diffs are equal → continue pattern
        # Example: 4 → 6 → 8 → 10 (diff = +2)
        # ------------------------------------
        if len(diffs) >= 3:
            d1, d2, d3 = diffs[-3], diffs[-2], diffs[-1]

            if d1 == d2 == d3:
                # Continue same difference pattern
                return (digits[-1] + d3) % 10

        # ------------------------------------
        # BASIC TREND RULE (Use last 2 digits)
        # last=7, prev=5 → diff=+2 → next=9
        # last=3, prev=6 → diff=-3 → next=0
        # ------------------------------------
        last = digits[-1]
        prev = digits[-2]
        diff = last - prev
        next_digit = (last + diff) % 10

        return next_digit
