# Gemini Project Helper

This file contains important information for the Gemini agent to work effectively on this project.

## Development Environment

This project uses Docker Compose to run a MySQL database for local development.

**To start the development environment:**

```bash
docker-compose up -d
```

This will start a MySQL container. The application is configured via the `.env` file to connect to this container.

## Python Virtual Environment

All Python scripts and tests in this project must be run within the activated virtual environment to ensure access to the correct dependencies. It is recommended to use Python 3.13.

**To activate the virtual environment:**

```bash
# Create with Python 3.13
python3.13 -m venv venv
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

## Database

The project uses a MySQL database to store complaint data. The schema is defined in `repository.py` and documented in `README.md`. When running locally, use the provided Docker Compose setup as described above.

## Environment Variables

This project uses a `.env` file for managing environment variables. You can copy the `.env.example` file to create your own `.env` file.

- `DB_HOST`: (for MySQL)
- `DB_USER`: (for MySQL)
- `DB_PASSWORD`: (for MySQL)
- `DB_NAME`: (for MySQL)

## Developer Notes

When a new feature is added or an existing feature is modified, please update the `README.md` file to reflect the changes. This will help new developers understand the project and its current state.