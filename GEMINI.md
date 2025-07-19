# Gemini Project Helper

This file contains important information for the Gemini agent to work effectively on this project.

## Python Virtual Environment

All Python scripts and tests in this project must be run within the activated virtual environment to ensure access to the correct dependencies.

**To activate the virtual environment:**

```bash
source venv/bin/activate
```

**Required packages:**

```bash
pip install selenium webdriver-manager mysql-connector-python python-dotenv
```

**Example of running a script:**

```bash
source venv/bin/activate && python3 pmc_complaint_checker_v2.py T60137 T60268
```

## Running Tests

All tests are located in the `tests/` directory.

**To run the database test:**

```bash
source venv/bin/activate && python3 tests/test_database.py
```

**To run the website test:**

```bash
source venv/bin/activate && python3 tests/test_website.py
```

## Environment Variables

This project uses a `.env` file for managing environment variables. You can copy the `.env.example` file to create your own `.env` file.

- `DB_TYPE`: `sqlite` or `mysql`
- `DB_HOST`: (for MySQL)
- `DB_USER`: (for MySQL)
- `DB_PASSWORD`: (for MySQL)
- `DB_NAME`: (for MySQL)

## Developer Notes

When a new feature is added or an existing feature is modified, please update the `README.md` file to reflect the changes. This will help new developers understand the project and its current state.
