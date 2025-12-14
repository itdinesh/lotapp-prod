from bs4 import BeautifulSoup
from datetime import datetime
from database_manager import DatabaseManager


# ---------------------------------------------------------
# DIGIT EXTRACTION
# ---------------------------------------------------------
def extract_digits(number: str):
    AAA_first = number[0]
    AA_second = number[1]
    A_third = number[2]
    B_fourth = number[3]
    C_last = number[4]

    last4 = number[1:]     # "1620"
    last3 = number[2:]     # "620"

    last2_ab = A_third + B_fourth   # "62"
    last2_bc = B_fourth + C_last    # "20"
    last2_ac = A_third + C_last     # "60"

    return {
        "aaa_first": AAA_first,
        "aa_second": AA_second,
        "a_third": A_third,
        "b_fourth": B_fourth,
        "c_last": C_last,
        "last4": last4,
        "last3": last3,
        "ab": last2_ab,
        "bc": last2_bc,
        "ac": last2_ac
    }


# ---------------------------------------------------------
# DATE PARSER → Sort Helper
# ---------------------------------------------------------
def parse_date(date_str: str):
    """
    Input:  "5 December 2025"
    Output: datetime(2025, 12, 5)
    """
    return datetime.strptime(date_str, "%d %B %Y")


# ---------------------------------------------------------
# PARSE HTML AND EXTRACT LOTTERY ROWS
# ---------------------------------------------------------
def parse_lottery_html(html_path: str, lottery_name: str):
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    results = []
    tables = soup.find_all("table", class_="lottery_chart_table")

    for table in tables:
        for row in table.find("tbody").find_all("tr"):

            cols = row.find_all("td")
            if len(cols) < 2:
                continue

            date_text = cols[0].text.strip()
            winner_text = cols[1].text.strip()

            try:
                prefix, number = winner_text.split()
            except:
                continue

            number = number.strip()
            digits = extract_digits(number)

            # Convert and keep sorting reference
            dt = parse_date(date_text)

            results.append({
                "sort_key": dt,                 # used only for sorting
                "lottery_name": lottery_name,
                "date": date_text,
                "time": "6 PM",
                "winner": winner_text,

                "aaa_first": digits["aaa_first"],
                "aa_second": digits["aa_second"],
                "a_third": digits["a_third"],
                "b_fourth": digits["b_fourth"],
                "c_last": digits["c_last"],
                "last4": digits["last4"],
                "last3": digits["last3"],
                "ab": digits["ab"],
                "bc": digits["bc"],
                "ac": digits["ac"]
            })

    # SORT BY SORT_KEY (year → month → day)
    results.sort(key=lambda x: x["sort_key"])

    return results


# ---------------------------------------------------------
# MAIN EXECUTION
# ---------------------------------------------------------
if __name__ == "__main__":
    db = DatabaseManager("lottery.db")

    rows = parse_lottery_html(
        html_path="lottery.html",
        lottery_name="Nagaland Dear 6 PM"
    )

    db.store_lottery_data(rows)

    print("🎉 Lottery Import Completed Successfully!")
