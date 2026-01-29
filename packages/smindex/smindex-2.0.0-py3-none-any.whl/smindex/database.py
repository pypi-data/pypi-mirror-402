import sqlite3
import numpy as np
from typing import Optional


create_schema = [
    """
    -- Table to store SMI data paths by date
    CREATE TABLE IF NOT EXISTS smi_data (
        id INTEGER PRIMARY KEY,
        date INTEGER,
        path TEXT
    );
    """,
    """
    -- Index on date for faster queries
    CREATE INDEX IF NOT EXISTS idx_date ON smi_data (date);
    """,
    """
    -- Table to store substorm event data
    CREATE TABLE IF NOT EXISTS substorms (
        id INTEGER PRIMARY KEY,
        date INTEGER,
        ut REAL,
        timestamp REAL,
        mlt REAL,
        mlat REAL,
        glon REAL,
        glat REAL,
        source TEXT
    );
    """,
    """
    -- Index on date for substorms table
    CREATE INDEX IF NOT EXISTS idx_substorm_date ON substorms (date);
    """
]


class SMIDatabase:
    """
    Class to manage the SQLite database for SMI data and substorm events.
    """

    def __init__(self, db_path: str) -> None:
        """
        Initialize the database connection and create tables if they don't exist.

        Inputs
        ======
        db_path : str
            Path to the SQLite database file.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.initialize()

    def initialize(self) -> None:
        """
        Create the necessary tables in the database if they do not already exist.
        """

        for item in create_schema:
            self.cursor.execute(item)
        self.conn.commit()

    def get_date(self, date: int) -> str | None:
        """
        Retrieve the file path for a given date.

        Inputs
        ======
        date : int
            Date in YYYYMMDD format.

        Outputs
        =======
        path : str or None
            File path associated with the date, or None if not found.
        """

        date = int(date)
        self.cursor.execute("SELECT path FROM smi_data WHERE date=?", (date,))
        result = self.cursor.fetchone()
        print(result)
        return result[0] if result else None

    def insert_date(self, date: int, path: str) -> None:
        """
        Insert a new date and file path into the database.

        Inputs
        ======
        date : int
            Date in YYYYMMDD format.
        path : str
            File path to be associated with the date.
        """

        date = int(date)
        if self.get_date(date) is not None:
            self.overwrite_date(date, path)
            return
        self.cursor.execute(
            "INSERT INTO smi_data (date, path) VALUES (?, ?)", (date, path)
        )
        self.conn.commit()

    def overwrite_date(self, date: int, path: str) -> None:
        """
        Overwrite the file path for an existing date in the database.

        Inputs
        ======
        date : int
            Date in YYYYMMDD format.
        path : str
            New file path to be associated with the date.
        """
        date = int(date)
        path = str(path)
        self.cursor.execute(
            "UPDATE smi_data SET path = ? WHERE date = ?", (path, date)
        )
        self.conn.commit()

    def check_existing_dates(self, dates: list[int]) -> set[int]:
        """
        Check which dates from a list already exist in the database.

        Inputs
        ======
        dates : list of int
            List of dates in YYYYMMDD format.

        Outputs
        =======
        existing_dates : set of int
            Set of dates that already exist in the database.
        """
        dates = [int(d) for d in dates]
        placeholders = ','.join("?" for _ in dates)
        query = f"SELECT date FROM smi_data WHERE date IN ({placeholders})"
        print(query)
        self.cursor.execute(query, dates)
        results = self.cursor.fetchall()
        print(results)
        return {row[0] for row in results}

    def insert_substorms(self, data: np.recarray) -> None:
        """
        Insert substorm event data into the database.

        Inputs
        ======
        data : np.recarray
            Structured numpy recarray containing substorm event data.
        """

        sql = """
            INSERT INTO substorms
            (date, ut, timestamp, mlt, mlat, glon, glat, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        rows = [
            (
                int(row['date']),
                float(row['ut']),
                float(row['timestamp']),
                float(row['mlt']),
                float(row['mlat']),
                float(row['glon']),
                float(row['glat']),
                str(row['source']),
            )
            for row in data
        ]

        self.cursor.executemany(sql, rows)
        self.conn.commit()

    def read_substorms(self, start_date: Optional[int] = None, end_date: Optional[int] = None) -> np.recarray:
        """
        Read substorm events from the database within an optional date range.

        Inputs
        ======
        start_date : int, optional
            Start date in YYYYMMDD format. If None, no lower bound is applied.
        end_date : int, optional
            End date in YYYYMMDD format. If None, no upper bound is applied.

        Outputs
        =======
        rows : np.recarray
            Structured numpy recarray containing the retrieved substorm events.

        """

        if start_date and end_date:
            self.cursor.execute(
                "SELECT * FROM substorms WHERE date BETWEEN ? AND ?",
                (start_date, end_date)
            )
        elif start_date:
            self.cursor.execute(
                "SELECT * FROM substorms WHERE date >= ?",
                (start_date,)
            )
        elif end_date:
            self.cursor.execute(
                "SELECT * FROM substorms WHERE date <= ?",
                (end_date,)
            )
        else:
            self.cursor.execute("SELECT * FROM substorms")
        rows = self.cursor.fetchall()
        return rows
