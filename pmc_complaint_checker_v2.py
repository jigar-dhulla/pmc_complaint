#!/usr/bin/env python3
"""
PMC Complaint Status Checker V2
Improved version that handles AJAX loading and dynamic content
"""

import sys
import time
import csv
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def setup_driver():
    """
    Set up Chrome WebDriver with headless options for efficiency.
    Uses webdriver-manager to automatically download and manage ChromeDriver.
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    try:
        # webdriver-manager will automatically download the correct ChromeDriver version
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        print("Please ensure Chrome is installed.")
        print("If Chrome is installed but you still see errors, try:")
        print("  - Installing Chrome: brew install --cask google-chrome")
        print("  - Updating Chrome to the latest version")
        sys.exit(1)
    
    return driver


def validate_token(token):
    """
    Validate that token starts with 'T' followed by digits.
    """
    return token.startswith('T') and token[1:].isdigit() and len(token) > 1


def extract_token_details_from_table(driver):
    """
    Extract details from the main token details table after submission.
    """
    details = {}
    
    try:
        # Wait for table with data to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//table[@id='calander-dataTables']//tbody[@id='table-data']/tr"))
        )
        
        # Get the first row of data from the table
        table_rows = driver.find_elements(By.XPATH, "//table[@id='calander-dataTables']//tbody[@id='table-data']/tr")
        
        if table_rows and len(table_rows) > 0:
            # Get the first row (should contain our token data)
            first_row = table_rows[0]
            cols = first_row.find_elements(By.TAG_NAME, "td")
            
            if len(cols) >= 7:
                details['sr_no'] = cols[0].text.strip()
                details['token_no'] = cols[1].text.strip()
                details['date'] = cols[2].text.strip()
                details['description'] = cols[3].text.strip()
                details['location'] = cols[4].text.strip()
                details['complaint_type'] = cols[5].text.strip()
                details['status'] = cols[6].text.strip()
                
                # Check if there's a track button
                track_buttons = cols[7].find_elements(By.TAG_NAME, "button") if len(cols) > 7 else []
                if track_buttons:
                    details['has_track_button'] = True
                    details['track_button_id'] = track_buttons[0].get_attribute('id')
                else:
                    details['has_track_button'] = False
    
    except TimeoutException:
        print("Timeout waiting for table data to load")
    except Exception as e:
        print(f"Error extracting token details from table: {e}")
    
    return details


def extract_track_details(driver, track_button_id):
    """
    Click the track button and extract tracking details from the modal.
    """
    track_info = {
        'overall_info': {},
        'tracking_details': []
    }
    
    try:
        # Click the track button
        track_button = driver.find_element(By.ID, track_button_id)
        driver.execute_script("arguments[0].click();", track_button)
        
        # Wait for modal to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "modalComplaintTrack"))
        )
        time.sleep(2)  # Allow modal to fully load
        
        # Extract overall info from modal
        token_elem = driver.find_element(By.ID, "track_tokenNo")
        if token_elem:
            track_info['overall_info']['token_no'] = token_elem.text.strip()
        
        status_elem = driver.find_element(By.ID, "track_status")
        if status_elem:
            track_info['overall_info']['status'] = status_elem.text.strip()
        
        category_elem = driver.find_element(By.ID, "track_complaintcategory")
        if category_elem:
            track_info['overall_info']['complaint_category'] = category_elem.text.strip()
        
        expected_date_elem = driver.find_element(By.ID, "track_expected_date")
        if expected_date_elem:
            track_info['overall_info']['expected_resolved_date'] = expected_date_elem.text.strip()
        
        # Extract tracking details from table
        track_rows = driver.find_elements(By.XPATH, "//tbody[@id='track']/tr")
        
        for row in track_rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 11:
                track_detail = {
                    'sr': cols[0].text.strip(),
                    'ticket_date': cols[1].text.strip(),
                    'status': cols[2].text.strip(),
                    'previous_status': cols[3].text.strip(),
                    'complaint_type_detail': cols[4].text.strip(),
                    'office': cols[5].text.strip(),
                    'department': cols[6].text.strip(),
                    'user': cols[7].text.strip(),
                    'remark': cols[8].text.strip(),
                    'action_date': cols[9].text.strip(),
                    'advice': cols[10].text.strip(),
                    'current_action': cols[11].text.strip() if len(cols) > 11 else ''
                }
                track_info['tracking_details'].append(track_detail)
    
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
        'token': token,
        'status': 'Failed',
        'error': None,
        'token_details': {},
        'complaint_track': {}
    }
    
    try:
        # Navigate to the website
        driver.get(url)
        time.sleep(2)  # Allow page to load
        
        # Find and fill the token input field
        try:
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "tokenNo"))
            )
            search_box.clear()
            search_box.send_keys(token)
            
            # Find and click the search button
            search_button = driver.find_element(By.ID, "btnSearch")
            search_button.click()
            
            # Wait for results
            time.sleep(3)
            
            # Check if any data is loaded in the table
            token_details = extract_token_details_from_table(driver)
            
            if token_details:
                result['token_details'] = token_details
                result['status'] = token_details.get('status', 'Unknown')
                
                # If there's a track button, click it to get more details
                if token_details.get('has_track_button') and token_details.get('track_button_id'):
                    track_info = extract_track_details(driver, token_details['track_button_id'])
                    if track_info:
                        result['complaint_track'] = track_info
            else:
                # Check if there's an error message or no data
                try:
                    # Check if table is empty
                    table_body = driver.find_element(By.ID, "table-data")
                    if not table_body.text.strip():
                        result['error'] = 'No data found for this token'
                except:
                    result['error'] = 'Could not find any data for this token'
        
        except TimeoutException:
            result['error'] = 'Timeout waiting for page elements'
        except NoSuchElementException as e:
            result['error'] = f'Element not found: {str(e)}'
        except Exception as e:
            result['error'] = f'Error processing token: {str(e)}'
    
    except Exception as e:
        result['error'] = f'Failed to load website: {str(e)}'
    
    return result


def save_to_csv(results):
    """
    Save results to CSV file with detailed columns.
    """
    filename = 'pmc_complaint_statuses.csv'
    
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'token', 'overall_status', 'date', 'description', 'location',
            'complaint_type', 'complaint_category', 'expected_resolved_date',
            'latest_action_date', 'latest_advice', 'latest_remark', 'error'
        ]
        
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                'token': result['token'],
                'overall_status': result.get('status', 'Failed'),
                'date': result['token_details'].get('date', ''),
                'description': result['token_details'].get('description', ''),
                'location': result['token_details'].get('location', ''),
                'complaint_type': result['token_details'].get('complaint_type', ''),
                'complaint_category': result['complaint_track'].get('overall_info', {}).get('complaint_category', ''),
                'expected_resolved_date': result['complaint_track'].get('overall_info', {}).get('expected_resolved_date', ''),
                'latest_action_date': '',
                'latest_advice': '',
                'latest_remark': '',
                'error': result.get('error', '')
            }
            
            # Get latest tracking details if available
            tracking_details = result.get('complaint_track', {}).get('tracking_details', [])
            if tracking_details:
                latest = tracking_details[-1]
                row['latest_action_date'] = latest.get('action_date', '')
                row['latest_advice'] = latest.get('advice', '')
                row['latest_remark'] = latest.get('remark', '')
            
            writer.writerow(row)
    
    print(f"\nResults saved to {filename}")


def print_results(result):
    """
    Print results in a readable format.
    """
    print(f"\n{'='*60}")
    print(f"Token: {result['token']}")
    print(f"Status: {result.get('status', 'Failed')}")
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    if result.get('token_details'):
        print("\nToken Details:")
        for key, value in result['token_details'].items():
            if key not in ['has_track_button', 'track_button_id', 'sr_no']:
                print(f"  {key}: {value}")
    
    if result.get('complaint_track') and result['complaint_track'].get('overall_info'):
        print("\nComplaint Overview:")
        for key, value in result['complaint_track']['overall_info'].items():
            print(f"  {key}: {value}")
    
    if result.get('complaint_track') and result['complaint_track'].get('tracking_details'):
        print("\nTracking History:")
        for detail in result['complaint_track']['tracking_details']:
            print(f"  - {detail.get('action_date', 'N/A')}: {detail.get('status', 'N/A')} - {detail.get('advice', 'N/A')}")


def main():
    """
    Main function to execute the script.
    """
    print("PMC Complaint Status Checker V2")
    print("="*60)
    
    # Get token input
    if len(sys.argv) > 1:
        # Command line argument provided
        token_input = sys.argv[1]
    else:
        # Prompt user for input
        print("Enter token numbers (comma-separated, e.g., T60137,T12345,T67890):")
        token_input = input().strip()
    
    if not token_input:
        print("No tokens provided. Exiting.")
        return
    
    # Parse and validate tokens
    tokens = [token.strip() for token in token_input.split(',')]
    valid_tokens = []
    
    for token in tokens:
        if validate_token(token):
            valid_tokens.append(token)
        else:
            print(f"Invalid token format: {token} (must start with 'T' followed by digits)")
    
    if not valid_tokens:
        print("No valid tokens to process. Exiting.")
        return
    
    print(f"\nProcessing {len(valid_tokens)} token(s)...")
    
    # Set up driver
    driver = setup_driver()
    results = []
    
    try:
        # Process each token
        for i, token in enumerate(valid_tokens, 1):
            print(f"\n[{i}/{len(valid_tokens)}] Processing token: {token}")
            
            result = process_token(driver, token)
            results.append(result)
            
            # Print results immediately
            print_results(result)
            
            # Add delay between requests (except for last one)
            if i < len(valid_tokens):
                print("\nWaiting before next request...")
                time.sleep(3)
        
        # Save all results to CSV
        if results:
            save_to_csv(results)
            
            # Also save as JSON for more detailed data
            json_filename = 'pmc_complaint_statuses.json'
            with open(json_filename, 'w', encoding='utf-8') as jsonfile:
                json.dump(results, jsonfile, indent=2, ensure_ascii=False)
            print(f"Detailed results also saved to {json_filename}")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Saving partial results...")
        if results:
            save_to_csv(results)
    
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    
    finally:
        # Clean up
        driver.quit()
        print("\nProcessing complete.")


if __name__ == "__main__":
    main()
