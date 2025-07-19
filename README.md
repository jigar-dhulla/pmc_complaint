# PMC Complaint Status Checker

This Python script automates checking the status of multiple PMC (Pune Municipal Corporation) complaint token numbers from their official website.

## Features

- Automated web scraping using Selenium and BeautifulSoup
- Supports multiple token numbers in a single run
- Runs in headless mode (no browser window)
- Saves results to a SQLite database and JSON file
- Comprehensive error handling
- Detailed status tracking and history

## Prerequisites

1. **Python 3.x** installed
2. **Google Chrome** browser installed
3. **ChromeDriver** installed

## Installation

### 1. Install Chrome (if not already installed)

On macOS:
```bash
brew install --cask google-chrome
```

### 2. Install ChromeDriver

On macOS with Homebrew:
```bash
brew install --cask chromedriver
```

After installation, you may need to allow ChromeDriver in System Preferences:
- Go to System Preferences > Security & Privacy
- Click "Allow Anyway" for chromedriver

Alternatively, download manually from: https://chromedriver.chromium.org/

### 3. Set up Python environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install selenium beautifulsoup4 webdriver-manager
```

## Usage

### Command Line Usage

```bash
# With virtual environment activated
python pmc_complaint_checker_v2.py "T60137,T60268"

# Or make it executable
./pmc_complaint_checker_v2.py "T60137,T60268"
```

### Interactive Usage

If you run the script without arguments, it will prompt you for token numbers:

```bash
python pmc_complaint_checker_v2.py
```

Then enter tokens when prompted:
```
Enter token numbers (comma-separated, e.g., T60137,T12345,T67890): T60137,T12345
```

## Token Format

- Tokens must start with 'T' followed by digits (e.g., T60137)
- Multiple tokens should be comma-separated
- Invalid tokens will be skipped with a warning

## Output

The script generates two output files:

1. **pmc_complaints.db** - A SQLite database containing the structured complaint data.
2. **pmc_complaint_statuses.json** - Complete detailed data in JSON format.

## Database Schema

The database (`pmc_complaints.db`) contains two tables:

### `complaints`

| Column | Type | Description |
|---|---|---|
| `token` | `TEXT` | The complaint token number (Primary Key) |
| `status` | `TEXT` | The current status of the complaint |
| `description` | `TEXT` | The complaint description |
| `location` | `TEXT` | The location of the complaint |
| `complaint_type` | `TEXT` | The type of complaint |
| `complaint_category` | `TEXT` | The category of the complaint |
| `expected_resolved_date` | `TEXT` | The expected resolution date |

### `tracking_history`

| Column | Type | Description |
|---|---|---|
| `id` | `INTEGER` | The unique ID of the tracking record (Primary Key) |
| `token` | `TEXT` | The complaint token number (Foreign Key to `complaints.token`) |
| `action_date` | `TEXT` | The date of the tracking action |
| `status` | `TEXT` | The status at the time of the tracking action |
| `remark` | `TEXT` | Any remarks associated with the tracking action |

## For New Developers

This project uses a repository pattern to interact with the database. The `repository.py` file contains the database logic, and the `SQLiteRepository` class implements the repository for SQLite.

If you need to change the database schema, you will need to:

1.  Update the `create_tables` method in `repository.py`.
2.  Delete the existing `pmc_complaints.db` file. The script will automatically create a new one with the updated schema on its next run.

To validate the database logic, you can run the tests in `test_database.py`:

```bash
python test_database.py
```

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

## License

This script is for educational and personal use only. Please respect the website's terms of service and avoid making excessive requests.
