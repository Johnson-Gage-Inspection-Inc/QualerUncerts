import requests
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from getpass import getpass
from time import sleep
from dotenv import load_dotenv
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException

# Load environment variables from .env file
load_dotenv()

# Set up database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")

# Set up Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)
driver.set_page_load_timeout(30)  # Timeout for Selenium


def show_progress(iterable, desc, unit, leave=True):
    """Wrapper for tqdm progress bar."""
    return tqdm(iterable, desc=desc, dynamic_ncols=True, unit=unit, leave=leave)


def main():
    login()
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    ServiceGroupIds = fetch_and_save_service_capabilities()
    TechniqueIds = fetch_and_save_technique_ids()

    # Use multithreading to speed up data fetching and writing
    for techniqueId in show_progress(TechniqueIds, desc="Techniques", unit="technique"):
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for serviceGroupId in ServiceGroupIds:
                futures.append(
                    executor.submit(
                        fetch_and_insert_uncertainty_budgets,
                        serviceGroupId,
                        techniqueId,
                    )
                )

            for _ in show_progress(
                futures, desc="Service Groups", unit="service group"
            ):
                _.result()  # Ensures exceptions are raised if any occur

    print("Data has been inserted into the database.")


def login():
    driver.get("https://jgiquality.qualer.com/login")
    username = os.getenv("QUALER_USERNAME") or input("Enter Qualer Email: ")
    password = os.getenv("QUALER_PASSWORD") or getpass("Enter Qualer Password: ")

    driver.find_element(By.ID, "Email").send_keys(username)
    driver.find_element(By.ID, "Password").send_keys(password + Keys.RETURN)

    sleep(5)
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
    """Fetch 'ServiceCapabilities' JSON."""
    url = "https://jgiquality.qualer.com/ServiceType/ServiceCapabilities"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)["views"]


def getTechniquesList():
    """Fetch 'TechniquesList' JSON."""
    url = "https://jgiquality.qualer.com/ServiceGroupTechnique/TechniquesList"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)


def getUncertaintyBudgets(serviceGroupId, techniqueId, retries=3):
    """Fetch UncertaintyBudgets JSON with retry for stale element issues."""
    url = f"https://jgiquality.qualer.com/ServiceGroupTechnique/UncertaintyBudgets?serviceGroupId={serviceGroupId}&techniqueId={techniqueId}"

    for attempt in range(retries):
        try:
            driver_get(url)
            data = driver.find_element(By.TAG_NAME, "pre").text
            return json.loads(data)["Data"]
        except StaleElementReferenceException:
            if attempt < retries - 1:
                print(
                    f"Stale element encountered. Retrying ({attempt + 1}/{retries})..."
                )
                sleep(2)  # Small delay before retrying
            else:
                raise  # Raise the error if all retries fail


def fetch_and_insert_uncertainty_budgets(serviceGroupId, techniqueId):
    """Fetch uncertainty budgets and insert directly into the database in small chunks."""
    if uncertainty_budgets := getUncertaintyBudgets(serviceGroupId, techniqueId):
        for row in uncertainty_budgets:
            row["ServiceGroupId"] = serviceGroupId
            row["TechniqueId"] = techniqueId

        df = pd.DataFrame(uncertainty_budgets)

        with engine.connect() as conn:
            for chunk in range(0, len(df), 500):  # Insert in batches of 500
                df.iloc[chunk: chunk + 500].to_sql(
                    "uncertainty_budgets", conn, if_exists="append", index=False
                )
        del df


def fetch_and_save_technique_ids():
    """Fetch technique IDs."""
    techniques_list = getTechniquesList()
    return [technique["TechniqueId"] for technique in techniques_list]


def fetch_and_save_service_capabilities():
    """Fetch service group IDs."""
    service_capabilities = getServiceCapabilities()
    return [service["ServiceGroupId"] for service in service_capabilities]


if __name__ == "__main__":
    main()
