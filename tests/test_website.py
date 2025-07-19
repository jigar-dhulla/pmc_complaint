#!/usr/bin/env python3
"""
Test script to inspect the PMC website structure
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time


def test_website():
    # Set up driver (not headless for debugging)
    chrome_options = Options()
    # Run in headless mode
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")

    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Navigate to the website
        url = "https://complaint.pmc.gov.in/rptTokenDetailsByTokenCitizen"
        print(f"Loading URL: {url}")
        driver.get(url)

        # Wait for page to load
        time.sleep(3)

        # Get page source
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Try to find all input fields
        print("\n=== All Input Fields ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, inp in enumerate(inputs):
            print(f"Input {i}:")
            print(f"  ID: {inp.get_attribute('id')}")
            print(f"  Name: {inp.get_attribute('name')}")
            print(f"  Type: {inp.get_attribute('type')}")
            print(f"  Placeholder: {inp.get_attribute('placeholder')}")
            print(f"  Class: {inp.get_attribute('class')}")
            print()

        # Try to find all buttons
        print("\n=== All Buttons ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, btn in enumerate(buttons):
            print(f"Button {i}:")
            print(f"  Text: {btn.text}")
            print(f"  ID: {btn.get_attribute('id')}")
            print(f"  Class: {btn.get_attribute('class')}")
            print()

        # Also check for input type="submit"
        submit_buttons = driver.find_elements(By.XPATH, "//input[@type='submit']")
        for i, btn in enumerate(submit_buttons):
            print(f"Submit Button {i}:")
            print(f"  Value: {btn.get_attribute('value')}")
            print(f"  ID: {btn.get_attribute('id')}")
            print(f"  Name: {btn.get_attribute('name')}")
            print()

        # Save page source for inspection
        with open("tests/pmc_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("\nPage source saved to pmc_page_source.html")

        # Keep browser open for 10 seconds to inspect
        print("\nBrowser will close in 10 seconds...")
        time.sleep(10)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()


if __name__ == "__main__":
    test_website()
