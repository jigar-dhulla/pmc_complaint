import json
import os
import mysql.connector

class Repository:
    def connect(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def save_complaint(self, complaint_data):
        raise NotImplementedError

class MySQLRepository(Repository):
    def __init__(self):
        self.conn = None

    def connect(self):
        self.conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME"),
        )
        self.create_tables()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        queries = [
            """
            CREATE TABLE IF NOT EXISTS complaints (
                token VARCHAR(255) PRIMARY KEY,
                status VARCHAR(255),
                description TEXT,
                location TEXT,
                complaint_type VARCHAR(255),
                complaint_category VARCHAR(255),
                expected_resolved_date VARCHAR(255)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tracking_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                token VARCHAR(255),
                action_date VARCHAR(255),
                status VARCHAR(255),
                remark TEXT,
                FOREIGN KEY (token) REFERENCES complaints (token)
            )
            """
        ]
        with self.conn.cursor() as cursor:
            for query in queries:
                cursor.execute(query)

    def save_complaint(self, complaint_data):
        token = complaint_data.get("token")
        if not token:
            return

        with self.conn.cursor() as cursor:
            cursor.execute(
                """INSERT INTO complaints 
                   (token, status, description, location, complaint_type, complaint_category, expected_resolved_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE status=VALUES(status), description=VALUES(description), location=VALUES(location), 
                   complaint_type=VALUES(complaint_type), complaint_category=VALUES(complaint_category), 
                   expected_resolved_date=VALUES(expected_resolved_date)""",
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

            tracking_details = complaint_data.get("complaint_track", {}).get("tracking_details", [])
            for record in tracking_details:
                cursor.execute(
                    """INSERT INTO tracking_history (token, action_date, status, remark) 
                       VALUES (%s, %s, %s, %s)""",
                    (
                        token,
                        record.get("action_date"),
                        record.get("status"),
                        record.get("remark"),
                    ),
                )
        self.conn.commit()
