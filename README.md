# PMC Complaint Status Checker

This Python script automates checking the status of multiple PMC (Pune Municipal Corporation) complaint token numbers from their official website.

## Features

- Automated web scraping using Selenium
- Supports multiple token numbers in a single run
- Runs in headless mode (no browser window)
- Saves results to a MySQL database and a JSON file
- Comprehensive error handling
- Detailed status tracking and history
- AWS Lambda compatible

## Prerequisites

1. **Python 3.13** installed
2. **Google Chrome** browser installed (for local development)

## Installation

### 1. Set up Python environment

It is recommended to use a virtual environment:

```bash
# Create virtual environment with Python 3.13
python3.13 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install selenium webdriver-manager mysql-connector-python python-dotenv
```

## Usage

### Command Line Usage (for local development)

You can pass one or more token numbers as command-line arguments:

```bash
# With virtual environment activated
python pmc_complaint_checker_v2.py T60137 T60268
```

### Using Docker for MySQL

For a consistent development environment, you can use the provided `docker-compose.yml` to run a MySQL server in a Docker container.

1.  **Install Docker and Docker Compose:**
    Follow the official installation instructions for your operating system.

2.  **Start the MySQL container:**
    ```bash
    docker-compose up -d
    ```

3.  **Configure your environment:**
    The project includes a `.env` file configured to connect to the Dockerized MySQL database. No changes are needed if you are using the Docker setup.

4.  **Stop the container:**
    ```bash
    docker-compose down
    ```

### AWS Lambda Usage

The script is designed to be deployed as an AWS Lambda function with a Python 3.13 runtime. The handler is `pmc_complaint_checker_v2.lambda_handler`.

**Build Script:**

The `scripts/build.sh` script prepares a `lambda_function.zip` file for deployment. This zip file contains the application code and its Python dependencies.

**Environment Variables:**

Set the following environment variables in your Lambda function configuration:

- `DB_TYPE`: `mysql`
- `DB_HOST`: Your MySQL database host
- `DB_USER`: Your MySQL database username
- `DB_PASSWORD`: Your MySQL database password
- `DB_NAME`: Your MySQL database name

**Event Payload:**

The Lambda function expects a JSON event with a `tokens` array:

```json
{
  "tokens": ["T60137", "T60268"]
}
```

## Token Format

- Tokens must start with 'T' followed by digits (e.g., T60137)
- Multiple tokens should be comma-separated (for local development) or in a JSON array (for Lambda)
- Invalid tokens will be skipped with a warning

## Output

The script generates a JSON file with detailed data:

In a Lambda environment, these files are saved to the `/tmp` directory.

## Database Schema

The database (`pmc_complaints` in MySQL) contains two tables:

### `complaints`

| Column | Type | Description |
|---|---|---|
| `token` | `VARCHAR(255)` | The complaint token number (Primary Key) |
| `status` | `VARCHAR(255)` | The current status of the complaint |
| `description` | `TEXT` | The complaint description |
| `location` | `TEXT` | The location of the complaint |
| `complaint_type` | `VARCHAR(255)` | The type of complaint |
| `complaint_category` | `VARCHAR(255)` | The category of the complaint |
| `expected_resolved_date` | `VARCHAR(255)` | The expected resolution date |

### `tracking_history`

| Column | Type | Description |
|---|---|---|
| `id` | `INT` | The unique ID of the tracking record (Primary Key) |
| `token` | `VARCHAR(255)` | The complaint token number (Foreign Key to `complaints.token`) |
| `action_date` | `VARCHAR(255)` | The date of the tracking action |
| `status` | `VARCHAR(255)` | The status at the time of the tracking action |
| `remark` | `TEXT` | Any remarks associated with the tracking action |





## Troubleshooting

### ChromeDriver Issues

If you get an error about ChromeDriver:

1. Check if ChromeDriver is installed:
   ```bash
   which chromedriver
   ```

2. Verify Chrome and ChromeDriver versions match:
   ```bash
   # Check Chrome version
   /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version
   
   # Check ChromeDriver version
   chromedriver --version
   ```

3. If versions don't match, update ChromeDriver:
   ```bash
   brew upgrade --cask chromedriver
   ```

### Permission Issues on macOS

If you see "chromedriver cannot be opened because it is from an unidentified developer":

1. Open System Preferences > Security & Privacy
2. Click "Allow Anyway" next to the chromedriver message
3. Or run in terminal:
   ```bash
   xattr -d com.apple.quarantine /opt/homebrew/bin/chromedriver
   ```

### Website Changes

If the script stops working, the website structure may have changed. You may need to:
1. Inspect the website to find new element IDs/classes
2. Update the selectors in the script accordingly

## Script Configuration

You can modify these settings in the script:

- **Headless mode**: Remove `--headless` from chrome_options to see the browser
- **Timeout**: Adjust WebDriverWait timeout (default: 10 seconds)
- **Delay between requests**: Change `time.sleep(3)` value (default: 3 seconds)

## Example Output

```
PMC Complaint Status Checker
============================================================
Processing 2 token(s)...

[1/2] Processing token: T60137

============================================================
Token: T60137
Status: Assigned

Token Details:
  token_no: T60137
  date: 07-07-2023 18:47 PM
  from_user: Cat Call Center
  description: Half done work on the footpath Khandare's bridge...
  assigned_to: Kharadi
  category: Bridge / Subway / Pedestrian
  status: Assigned

Complaint Overview:
  complaint_category: Bridge / Subway / Pedestrian
  expected_resolved_date: 16/07/2023 18:47 PM

Tracking History:
  - 10-07-2023: Forwarded - Auto Generated

Results saved to pmc_complaints.db
Detailed results also saved to pmc_complaint_statuses.json

Processing complete.
```

## Notes

- The script includes a 3-second delay between requests to avoid overwhelming the server
- If a token is invalid or has no data, it will be marked with an error message
- The script runs in headless mode by default (no browser window appears)
- All dates and times are preserved as they appear on the website
- Only valid tokens that exist in the PMC system will return results
- The V2 script can extract detailed tracking history by clicking the track button automatically

## TODO
- Make this script working on aws lambda.
  - to make it work on lambda, we need lambda environment on local so that we can troubleshoot quickly
- create eventbridge rule to run the lambda periodically


## License

This script is for educational and personal use only. Please respect the website's terms of service and avoid making excessive requests.
