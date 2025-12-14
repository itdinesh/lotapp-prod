import sqlite3
import threading


class DatabaseManager:
    def __init__(self, db_path="lottery.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()

    # -------------------------------------------------------
    # CONNECT
    # -------------------------------------------------------
    def connect(self):
        return sqlite3.connect(self.db_path)

    # -------------------------------------------------------
    # INIT DATABASE
    # -------------------------------------------------------
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS lottery_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lottery_name TEXT,
                    date_col TEXT,
                    time_col TEXT,
                    winner TEXT,

                    aaa_first TEXT,
                    aa_second TEXT,
                    a_third TEXT,
                    b_fourth TEXT,
                    c_last TEXT,

                    last4 TEXT,
                    last3 TEXT,
                    last2_ab TEXT,
                    last2_bc TEXT,
                    last2_ac TEXT
                )
            """)

            # Indexes for faster filtering
            c.execute("CREATE INDEX IF NOT EXISTS idx_date ON lottery_data(date_col)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_time ON lottery_data(time_col)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_lottery ON lottery_data(lottery_name)")

            conn.commit()

    # -------------------------------------------------------
    # STORE LOTTERY DATA
    # -------------------------------------------------------
    def store_lottery_data(self, rows):
        with self.lock:  # thread-safe writes
            conn = self.connect()
            cursor = conn.cursor()

            for row in rows:
                cursor.execute("""
                    INSERT INTO lottery_data (
                        lottery_name, date_col, time_col, winner,
                        aaa_first, aa_second, a_third, b_fourth, c_last,
                        last4, last3, last2_ab, last2_bc, last2_ac
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get("lottery_name"),
                    row.get("date"),
                    row.get("time"),
                    row.get("winner"),
                    row.get("aaa_first"),
                    row.get("aa_second"),
                    row.get("a_third"),
                    row.get("b_fourth"),
                    row.get("c_last"),
                    row.get("last4"),
                    row.get("last3"),
                    row.get("ab"),       # safe
                    row.get("bc"),
                    row.get("ac")
                ))

            conn.commit()
            conn.close()

    # -------------------------------------------------------
    # SORT HELPERS
    # -------------------------------------------------------
    DATE_SORT = """
        (
            substr(date_col, -4) || '-' ||
            CASE
                WHEN date_col LIKE '%January%' THEN '01'
                WHEN date_col LIKE '%February%' THEN '02'
                WHEN date_col LIKE '%March%' THEN '03'
                WHEN date_col LIKE '%April%' THEN '04'
                WHEN date_col LIKE '%May%' THEN '05'
                WHEN date_col LIKE '%June%' THEN '06'
                WHEN date_col LIKE '%July%' THEN '07'
                WHEN date_col LIKE '%August%' THEN '08'
                WHEN date_col LIKE '%September%' THEN '09'
                WHEN date_col LIKE '%October%' THEN '10'
                WHEN date_col LIKE '%November%' THEN '11'
                WHEN date_col LIKE '%December%' THEN '12'
                ELSE '00'
            END || '-' ||
            printf('%02d', CAST(substr(date_col, 1, instr(date_col, ' ') - 1) AS INTEGER))
        )
    """

    TIME_SORT = """
        CASE time_col
            WHEN '12.30 AM' THEN 1
            WHEN '1 PM' THEN 2
            WHEN '3 PM' THEN 3
            WHEN '5.30 PM' THEN 4
            WHEN '6 PM' THEN 5
            WHEN '7.30 PM' THEN 6
            WHEN '8 PM' THEN 7
            WHEN '9 PM' THEN 8
            WHEN '10 PM' THEN 9
            ELSE 8
        END
    """

    # -------------------------------------------------------
    # FILTER LISTS
    # -------------------------------------------------------
    def get_lottery_filters(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            c.execute("SELECT DISTINCT lottery_name FROM lottery_data ORDER BY lottery_name")
            names = [x[0] for x in c.fetchall()]

            c.execute(f"SELECT DISTINCT date_col FROM lottery_data ORDER BY {self.DATE_SORT} ASC")
            dates = [x[0] for x in c.fetchall()]

            c.execute(f"SELECT DISTINCT time_col FROM lottery_data ORDER BY {self.TIME_SORT} ASC")
            times = [x[0] for x in c.fetchall()]

        return {"lottery_names": names, "dates": dates, "times": times}

    # -------------------------------------------------------
    # PAGINATED VIEWER
    # -------------------------------------------------------
    def get_lottery_rows(self, lottery_name, date_col, time_col, page, page_size=3):

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            base = "FROM lottery_data WHERE 1=1"
            params = []

            if lottery_name:
                base += " AND lottery_name=?"
                params.append(lottery_name)

            if date_col:
                base += " AND date_col=?"
                params.append(date_col)

            if time_col:  # time_col is a LIST
                placeholders = ",".join(["?"] * len(time_col))
                base += f" AND time_col IN ({placeholders})"
                params.extend(time_col)

            query = f"""
                SELECT * {base}
                ORDER BY {self.DATE_SORT} DESC, {self.TIME_SORT} DESC
                LIMIT ? OFFSET ?
            """

            offset = (page - 1) * page_size

            c.execute(query, params + [page_size, offset])
            rows = c.fetchall()

            c.execute("SELECT COUNT(*) " + base, params)
            total = c.fetchone()[0]

        return rows, total

    # -------------------------------------------------------
    # FULL HISTORY (FOR PREDICTION ENGINE)
    # -------------------------------------------------------
    def get_all_history(self, time_filter=None):

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            base = "FROM lottery_data WHERE 1=1"
            params = []

            if time_filter:
                placeholders = ",".join(["?"] * len(time_filter))
                base += f" AND time_col IN ({placeholders})"
                params.extend(time_filter)

            q = f"""
                SELECT * {base}
                ORDER BY {self.DATE_SORT} ASC, {self.TIME_SORT} ASC
            """

            c.execute(q, params)
            rows = c.fetchall()

            # ❌ Remove last two rows
            # if len(rows) > 5:
            #     rows = rows[:-5]

            return rows

    # -------------------------------------------------------
    # LAST 4 RESULTS BLOCK
    # -------------------------------------------------------
    def get_last4(self, time_filter=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Handle "All" case
            if time_filter in (None, "", "ALL"):
                q = f"""
                    SELECT * FROM lottery_data
                    ORDER BY {self.DATE_SORT} DESC, {self.TIME_SORT} DESC
                    LIMIT 4
                """
                c.execute(q)
                return c.fetchall()

            # Filter by specific time
            q = f"""
                SELECT * FROM lottery_data
                WHERE time_col=?
                ORDER BY {self.DATE_SORT} DESC
                LIMIT 4
            """
            c.execute(q, [time_filter])
            return c.fetchall()
