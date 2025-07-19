
import unittest
import sqlite3
import json
import os
from repository import SQLiteRepository

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db_file = "test_pmc_complaints.db"
        # Ensure old test db is removed before a new test run
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
        self.repo = SQLiteRepository(self.db_file)
        self.repo.connect()

    def tearDown(self):
        self.repo.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_data_population(self):
        # Load test data from JSON file
        with open("pmc_complaint_statuses.json") as f:
            test_data = json.load(f)

        # Save to database
        for complaint in test_data:
            self.repo.save_complaint(complaint)

        # Verify data in complaints table
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM complaints")
            complaints = cursor.fetchall()
            self.assertEqual(len(complaints), 2, "Should be 2 complaints in the table")

            # Verify data in tracking_history table
            cursor.execute("SELECT * FROM tracking_history")
            tracking_history = cursor.fetchall()
            # Total tracking details from both tokens in the json file
            total_tracking_entries = len(test_data[0]['complaint_track']['tracking_details']) + len(test_data[1]['complaint_track']['tracking_details'])
            self.assertEqual(len(tracking_history), total_tracking_entries, "Should be a total of 14 tracking history entries")

if __name__ == "__main__":
    unittest.main()
