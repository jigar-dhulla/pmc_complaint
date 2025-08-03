#!/usr/bin/env python3
"""
PMC Complaint Status Checker V2
Improved version that handles AJAX loading and dynamic content
AWS Lambda compatible.
"""

import sys
import time
import json
import os
import argparse
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from selenium import webdriver
from repository import MySQLRepository
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def run_command(command):
    """Helper function to run a shell command and return its output for debugging."""
    try:
        print(f"RUNNING COMMAND: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception on non-zero exit
        )
        print(f"STDOUT:\n{result.stdout.strip()}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr.strip()}")
    except FileNotFoundError:
        print(f"Command not found: {command[0]}")
    except Exception as e:
        print(f"Error running command {' '.join(command)}: {e}")


def setup_driver():
    """
    Set up Chrome WebDriver, adapting to the execution environment.
    - In a container (like Lambda), it uses the pre-installed chromedriver.
    - For local execution, it uses webdriver-manager to download the driver.
    """
    print("--- Starting driver setup ---")

    chrome_options = Options()
    print("Setting Chrome options...")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
    )

    # Lambda/Docker specific options
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        print("Applying Lambda/Docker specific Chrome options.")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--no-zygote")
        chrome_options.add_argument("--single-process")
        chrome_options.add_argument("--user-data-dir=/tmp/user-data")
        chrome_options.add_argument("--data-path=/tmp/data-path")
        chrome_options.add_argument("--disk-cache-dir=/tmp/cache-dir")

    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    print("Chrome options set.")

    try:
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            print("Running in Lambda/Docker environment. Using pre-installed chromedriver.")
            
            chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
            chrome_path = os.environ.get("CHROME_PATH")

            # Verify paths and permissions
            if not os.path.exists(chromedriver_path):
                raise FileNotFoundError(f"Chromedriver not found at: {chromedriver_path}")
            if not os.access(chromedriver_path, os.X_OK):
                raise PermissionError(f"Chromedriver is not executable: {chromedriver_path}")
            if not os.path.exists(chrome_path):
                raise FileNotFoundError(f"Chrome binary not found at: {chrome_path}")

            chrome_options.binary_location = chrome_path
            
            service = Service(
                executable_path=chromedriver_path,
                service_args=["--verbose", "--log-path=/tmp/chromedriver.log"],
            )
        else:
            print("Running in local environment. Using webdriver-manager.")
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())

        print("Attempting to start webdriver.Chrome...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("webdriver.Chrome started successfully.")
        return driver

    except Exception as e:
        print("!!! FAILED to start webdriver.Chrome !!!")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {e}")
        
        # Log chromedriver output if available
        if os.path.exists("/tmp/chromedriver.log"):
            with open("/tmp/chromedriver.log", "r") as f:
                print("--- Chromedriver Log ---")
                print(f.read())
                print("------------------------")
        
        # Add more debug info
        run_command(["ls", "-l", "/opt/chrome-linux64/"])
        run_command(["ls", "-l", "/opt/chromedriver-linux64/"])
        run_command(["google-chrome", "--version"])
        run_command(["chromedriver", "--version"])
        
        raise e


def validate_token(token):
    """
    Validate that token starts with 'T' followed by digits.
    """
    return token.startswith("T") and token[1:].isdigit() and len(token) > 1


def extract_token_details_from_table(driver):
    """
    Extract details from the main token details table after submission.
    """
    details = {}
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//table[@id='calander-dataTables']//tbody[@id='table-data']/tr",
                )
            )
        )
        table_rows = driver.find_elements(
            By.XPATH, "//table[@id='calander-dataTables']//tbody[@id='table-data']/tr"
        )
        if table_rows and len(table_rows) > 0:
            first_row = table_rows[0]
            cols = first_row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 7:
                details["sr_no"] = cols[0].text.strip()
                details["token_no"] = cols[1].text.strip()
                details["date"] = cols[2].text.strip()
                details["description"] = cols[3].text.strip()
                details["location"] = cols[4].text.strip()
                details["complaint_type"] = cols[5].text.strip()
                details["status"] = cols[6].text.strip()
                track_buttons = (
                    cols[7].find_elements(By.TAG_NAME, "button")
                    if len(cols) > 7
                    else []
                )
                if track_buttons:
                    details["has_track_button"] = True
                    details["track_button_id"] = track_buttons[0].get_attribute("id")
                else:
                    details["has_track_button"] = False
    except TimeoutException:
        print("Timeout waiting for table data to load")
    except Exception as e:
        print(f"Error extracting token details from table: {e}")
    return _replace_empty_with_unknown(details)


def extract_track_details(driver, track_button_id):
    """
    Click the track button and extract tracking details from the modal.
    """
    track_info = {"overall_info": {}, "tracking_details": []}
    try:
        track_button = driver.find_element(By.ID, track_button_id)
        driver.execute_script("arguments[0].click();", track_button)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "modalComplaintTrack"))
        )
        time.sleep(3)
        token_elem = driver.find_element(By.ID, "track_tokenNo")
        if token_elem:
            track_info["overall_info"]["token_no"] = token_elem.text.strip()
        status_elem = driver.find_element(By.ID, "track_status")
        if status_elem:
            track_info["overall_info"]["status"] = status_elem.text.strip()
        category_elem = driver.find_element(By.ID, "track_complaintcategory")
        if category_elem:
            track_info["overall_info"][
                "complaint_category"
            ] = category_elem.text.strip()
        expected_date_elem = driver.find_element(By.ID, "track_expected_date")
        if expected_date_elem:
            track_info["overall_info"][
                "expected_resolved_date"
            ] = expected_date_elem.text.strip()
        track_rows = driver.find_elements(By.XPATH, "//tbody[@id='track']/tr")
        for row in track_rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 11:
                track_detail = {
                    "sr": cols[0].text.strip(),
                    "ticket_no": cols[1].text.strip(),
                    "ticket_date": cols[2].text.strip(),
                    "from_user": cols[3].text.strip(),
                    "complaints": cols[4].text.strip(),
                    "office": cols[5].text.strip(),
                    "department": cols[6].text.strip(),
                    "to_user": cols[7].text.strip(),
                    "remark": cols[8].text.strip(),
                    "action_date": cols[9].text.strip(),
                    "advice": cols[10].text.strip(),
                    "current_action": cols[11].text.strip() if len(cols) > 11 else "",
                }
                track_info["tracking_details"].append(track_detail)
    except TimeoutException:
        print("Timeout waiting for track modal to load")
    except Exception as e:
        print(f"Error extracting track details: {e}")
    return track_info


def process_token(driver, token):
    """
    Process a single token and extract its status details.
    """
    url = "https://complaint.pmc.gov.in/rptTokenDetailsByTokenCitizen"
    result = {
        "token": token,
        "status": "Failed",
        "error": None,
        "token_details": {},
        "complaint_track": {},
    }
    try:
        driver.get(url)
        time.sleep(2)
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "tokenNo"))
            )
            search_box.clear()
            search_box.send_keys(token)
            search_button = driver.find_element(By.ID, "btnSearch")
            search_button.click()
            time.sleep(3)
            token_details = extract_token_details_from_table(driver)
            if token_details:
                result["token_details"] = token_details
                result["status"] = token_details.get("status", "Unknown")
                if token_details.get("has_track_button") and token_details.get(
                    "track_button_id"
                ):
                    track_info = extract_track_details(
                        driver, token_details["track_button_id"]
                    )
                    if track_info:
                        result["complaint_track"] = track_info
            else:
                try:
                    table_body = driver.find_element(By.ID, "table-data")
                    if not table_body.text.strip():
                        result["error"] = "No data found for this token"
                except:
                    result["error"] = "Could not find any data for this token"
        except TimeoutException:
            result["error"] = "Timeout waiting for page elements"
        except NoSuchElementException as e:
            result["error"] = f"Element not found: {str(e)}"
        except Exception as e:
            result["error"] = f"Error processing token: {str(e)}"
    except Exception as e:
        result["error"] = f"Failed to load website: {str(e)}"
    return result


def print_results(result):
    """
    Print results in a readable format.
    """
    print(f"\n{'='*60}")
    print(f"Token: {result['token']}")
    print(f"Status: {result.get('status', 'Failed')}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    if result.get("token_details"):
        print("\nToken Details:")
        for key, value in result["token_details"].items():
            if key not in ["has_track_button", "track_button_id", "sr_no"]:
                print(f"  {key}: {value}")
    if result.get("complaint_track") and result["complaint_track"].get("overall_info"):
        print("\nComplaint Overview:")
        for key, value in result["complaint_track"]["overall_info"].items():
            print(f"  {key}: {value}")
    if result.get("complaint_track") and result["complaint_track"].get(
        "tracking_details"
    ):
        print("\nTracking History:")
        for detail in result["complaint_track"]["tracking_details"]:
            print(
                f"  - {detail.get('action_date', 'N/A')}: {detail.get('current_action', 'N/A')} - {detail.get('remark', 'N/A')}"
            )


def fetch_token_details(tokens):
    """
    Processes a list of tokens, saves the results to the database, and returns them.
    """
    driver = None
    results = []
    try:
        print("Database connection successful.")

        # 2. If connection is successful, setup the driver and scrape
        print(f"\nProcessing {len(tokens)} token(s)...")
        driver = setup_driver()

        for i, token in enumerate(tokens, 1):
            print(f"\n[{i}/{len(tokens)}] Processing token: {token}")
            result = process_token(driver, token)
            results.append(result)
            print_results(result)
            if i < len(tokens):
                print("\nWaiting before next request...")
                time.sleep(3)

    finally:
        if driver:
            driver.quit()

    return results


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    """
    load_dotenv()
    try:
        tokens = event.get("tokens", [])
        if not isinstance(tokens, list):
            tokens = [tokens]

        valid_tokens = [token for token in tokens if validate_token(token)]
        if not valid_tokens:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "No valid tokens provided."}),
            }

        # 1. Connect to the database first
        print("Connecting to MySQL database...")
        repo = MySQLRepository()
        repo.connect()

        # 2. Fetch Token Details
        results = fetch_token_details(valid_tokens)

        # 3. Save results to database
        for result in results:
            repo.save_complaint(result)
        repo.close()

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Successfully processed {len(results)} token(s).",
                    "results": results,
                },
                indent=2,
                ensure_ascii=False,
            ),
        }
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {"message": "An error occurred", "error": str(e)},
                indent=2,
                ensure_ascii=False,
            ),
        }


def main():
    """
    Main function for local execution.
    """
    load_dotenv()

    parser = argparse.ArgumentParser(description="PMC Complaint Status Checker")
    parser.add_argument(
        "tokens",
        nargs="+",
        help="One or more token numbers to check (e.g., T60137 T60268)",
    )
    args = parser.parse_args()

    valid_tokens = [token for token in args.tokens if validate_token(token)]
    if not valid_tokens:
        print("No valid tokens to process.")
        return

    try:
        # 1. Connect to the database first
        print("Connecting to MySQL database...")
        repo = MySQLRepository()
        repo.connect()

        # 2. Fetch Token Details
        results = fetch_token_details(valid_tokens)

        # 4. Save results to local JSON file
        date_now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        json_filename = f"pmc_complaint_statuses {date_now}.json"
        with open(json_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(results, jsonfile, indent=2, ensure_ascii=False)
        print(f"Detailed results also saved to {json_filename}")

        # 5. Save results to database
        for result in results:
            repo.save_complaint(result)
        repo.close()
        print("Results saved to the database.")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    finally:
        print("\nProcessing complete.")


def _replace_empty_with_unknown(data: dict) -> dict:
    """
    replaces empty string values in dicts with 'Unknown'.
    """
    for key, value in data.items():
        if value == "":
            data[key] = "Unknown"
    return data


if __name__ == "__main__":
    main()
