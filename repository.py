import sqlite3
import json

class Repository:
    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def save_complaint(self, complaint_data):
        raise NotImplementedError

class SQLiteRepository(Repository):
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_file)
        self.create_tables()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS complaints (
                token TEXT PRIMARY KEY,
                status TEXT,
                description TEXT,
                location TEXT,
                complaint_type TEXT,
                complaint_category TEXT,
                expected_resolved_date TEXT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tracking_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token TEXT,
                action_date TEXT,
                status TEXT,
                remark TEXT,
                FOREIGN KEY (token) REFERENCES complaints (token)
            )
            """
        ]
        with self.conn:
            for query in queries:
                self.conn.execute(query)

    def save_complaint(self, complaint_data):
        token = complaint_data.get("token")
        if not token:
            return

        with self.conn:
            # Insert into complaints table
            self.conn.execute(
                """INSERT OR REPLACE INTO complaints 
                   (token, status, description, location, complaint_type, complaint_category, expected_resolved_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    token,
                    complaint_data.get("status"),
                    complaint_data.get("token_details", {}).get("description"),
                    complaint_data.get("token_details", {}).get("location"),
                    complaint_data.get("token_details", {}).get("complaint_type"),
                    complaint_data.get("complaint_track", {}).get("overall_info", {}).get("complaint_category"),
                    complaint_data.get("complaint_track", {}).get("overall_info", {}).get("expected_resolved_date"),
                ),
            )

            # Insert into tracking_history table
            tracking_details = complaint_data.get("complaint_track", {}).get("tracking_details", [])
            for record in tracking_details:
                self.conn.execute(
                    """INSERT INTO tracking_history (token, action_date, status, remark) 
                       VALUES (?, ?, ?, ?)""",
                    (
                        token,
                        record.get("action_date"),
                        record.get("status"),
                        record.get("remark"),
                    ),
                )