import requests
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from getpass import getpass
from time import sleep
from dotenv import load_dotenv
import json
from tqdm import tqdm
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Create the directory if it doesn't exist
output_dir = "csv"
os.makedirs(output_dir, exist_ok=True)

# Set up Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)


# Load environment variables from .env file
load_dotenv()


def login():
    driver.get("https://jgiquality.qualer.com/login")

    # Get credentials from environment variables or prompt user
    username = os.getenv("QUALER_USERNAME") or input("Enter Qualer Email: ")
    password = os.getenv("QUALER_PASSWORD") or getpass("Enter Qualer Password: ")

    # Input credentials
    driver.find_element(By.ID, "Email").send_keys(username)
    driver.find_element(By.ID, "Password").send_keys(password + Keys.RETURN)

    # Allow time for login
    sleep(5)

    # Check if login was successful
    if "login" in driver.current_url:
        print("Login failed. Check credentials.")
        driver.quit()
        exit()


def driver_get(url):
    """Loads a URL and re-logins if Qualer prompts for authentication again."""
    driver.get(url)
    if "login" in driver.current_url.lower():
        print("Session expired or reauthentication needed. Logging in again...")
        login()
        driver.get(url)


def getServiceCapabilities():
    """Fetch 'ServiceCapabilities' JSON and return as a DataFrame."""
    url = "https://jgiquality.qualer.com/ServiceType/ServiceCapabilities"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)["views"]


def getTechniquesList():
    """Fetch 'TechniquesList' JSON and return as a DataFrame."""
    url = "https://jgiquality.qualer.com/ServiceGroupTechnique/TechniquesList"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)


def getUncertaintyBudgets(serviceGroupId, techniqueId):
    """Fetch UncertaintyBudgets JSON for a given ServiceGroup + Technique ID."""
    url = f"https://jgiquality.qualer.com/ServiceGroupTechnique/UncertaintyBudgets?serviceGroupId={serviceGroupId}&techniqueId={techniqueId}"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)["Data"]


def main():
    # Perform login
    login()

    # Extract cookies for requests session
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    # Fetch and save ServiceCapabilities
    service_capabilities = getServiceCapabilities()
    with open(
        os.path.join(output_dir, "ServiceCapabilities.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(service_capabilities[0].keys())
        for row in service_capabilities:
            writer.writerow(row.values())

    # Fetch and save TechniquesList
    techniques_list = getTechniquesList()
    with open(
        os.path.join(output_dir, "TechniquesList.csv"),
        "w",
        newline="",
        encoding="utf-8",
    ) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(techniques_list[0].keys())
        for row in techniques_list:
            writer.writerow(row.values())
    TechniqueIds = [technique["TechniqueId"] for technique in techniques_list]
    ServiceGroupIds = [service["ServiceGroupId"] for service in service_capabilities]

    def fetch_uncertainty_budgets(serviceGroupId, techniqueId):
        uncertainty_budgets = getUncertaintyBudgets(serviceGroupId, techniqueId)
        if uncertainty_budgets:
            for row in uncertainty_budgets:
                row["ServiceGroupId"] = serviceGroupId
                row["TechniqueId"] = techniqueId
            return uncertainty_budgets
        return []

    all_uncertainty_budgets = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for serviceGroupId in ServiceGroupIds:
            for techniqueId in TechniqueIds:
                futures.append(
                    executor.submit(
                        fetch_uncertainty_budgets, serviceGroupId, techniqueId
                    )
                )

        for future in tqdm(futures, desc="Fetching Uncertainty Budgets", dynamic_ncols=True, total=len(futures), unit="budgets"):
            result = future.result()
            if result:
                all_uncertainty_budgets.extend(result)

    # Convert to DataFrame and save as a single CSV file
    df = pd.DataFrame(all_uncertainty_budgets)
    df.to_csv(
        os.path.join(output_dir, "AllUncertaintyBudgets.csv"),
        index=False,
        encoding="utf-8",
    )

    print("Data has been saved to CSV files in the 'QualerUncerts/csv' directory.")


if __name__ == "__main__":
    main()
