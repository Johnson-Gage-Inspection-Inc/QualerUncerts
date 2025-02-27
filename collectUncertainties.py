import requests
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from getpass import getpass
from time import sleep

# Create the directory if it doesn't exist
output_dir = 'csv'
os.makedirs(output_dir, exist_ok=True)

# Set up Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)


def login():
    driver.get("https://jgiquality.qualer.com/login")

    # Input credentials
    driver.find_element(By.ID, "Email").send_keys(input("Enter Qualer Email: "))
    driver.find_element(By.ID, "Password").send_keys(getpass("Enter Qualer Password: ") + Keys.RETURN)

    # Allow time for login
    sleep(5)

    # Check if login was successful
    if "login" in driver.current_url:
        print("Login failed. Check credentials.")
        driver.quit()
        exit()


def main():
    # Perform login
    login()

    # Extract cookies for requests session
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])

    driver.quit()

    # Define headers
    headers = {
        "accept": "application/json",
        "x-requested-with": "XMLHttpRequest",
    }

    # Define the URLs
    urls = [
        "https://jgiquality.qualer.com/ServiceType/ServiceCapabilities",
        "https://jgiquality.qualer.com/ServiceGroupTechnique/TechniquesList"
    ]

    # Fetch data from each URL and save to CSV
    for url in urls:
        response = session.get(url, headers=headers)
        if response.status_code == 401:
            print(f"Unauthorized request: {url}. Check authentication.")
            continue

        data = response.json()
        file_name = url.split('/')[-1] + '.csv'
        output_file = os.path.join(output_dir, file_name)

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())

    # Define the combinations of serviceGroupId and techniqueId
    combinations = [
        (14319, 855),
        # Add more combinations as needed
    ]

    # Fetch data for each combination and save to CSV
    for serviceGroupId, techniqueId in combinations:
        url = f"https://jgiquality.qualer.com/ServiceGroupTechnique/UncertaintyBudgets?serviceGroupId={serviceGroupId}&techniqueId={techniqueId}"
        response = session.get(url, headers=headers)

        if response.status_code == 401:
            print(f"Unauthorized request: {url}. Check authentication.")
            continue

        data = response.json()
        file_name = f"UncertaintyBudgets_{serviceGroupId}_{techniqueId}.csv"
        output_file = os.path.join(output_dir, file_name)

        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(data[0].keys())
            for row in data:
                writer.writerow(row.values())

    print("Data has been saved to CSV files in the 'QualerUncerts/csv' directory.")


if __name__ == "__main__":
    main()
