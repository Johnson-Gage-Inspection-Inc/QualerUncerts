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
from sqlalchemy import create_engine
from sqlalchemy.engine.base import Connection
import pandas as pd
from selenium.common.exceptions import StaleElementReferenceException

# Load environment variables from .env file
load_dotenv()

# Set up database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")

# Set up Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--headless")  # Run in headless mode
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

    TechniqueIds = fetch_and_save_technique_ids()

    for techniqueId in tqdm(TechniqueIds, desc="Techniques", unit="technique"):
        fetch_and_insert_capablilites(techniqueId)

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


def getTechniquesList():
    """Fetch 'TechniquesList' JSON."""
    url = "https://jgiquality.qualer.com/ServiceGroupTechnique/TechniquesList"
    driver_get(url)
    data = driver.find_element(By.TAG_NAME, "pre").text
    return json.loads(data)


def getCapabilities(techniqueId, retries=3):
    """Fetch UncertaintyBudgets JSON with retry for stale element issues."""
    url = f"https://jgiquality.qualer.com/CertificationCapability/Capabilities_Read?sort=&group=&filter=&techniqueId={techniqueId}&certificationId=284"

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


def table_exists(table_name, conn: Connection):
    """Check if a table exists in the database."""
    query = f"""
    SELECT EXISTS (
        SELECT FROM information_schema.tables
        WHERE table_name = '{table_name}'
    );
    """
    result = conn.execute(query)
    return result.scalar()


def fetch_and_insert_capablilites(techniqueId):
    """Fetch uncertainty budgets and insert directly into the database in small chunks."""
    if capabilities := getCapabilities(techniqueId):
        for row in capabilities:
            row["TechniqueId"] = techniqueId

        df = pd.DataFrame(capabilities)
        for chunk in range(0, len(df), 500):  # Insert in batches of 500
            df.iloc[chunk: chunk + 500].to_sql(
                "capabilities", engine, if_exists="append", index=False
            )
        del df


def fetch_and_save_technique_ids():
    """Fetch technique IDs."""
    techniques_list = getTechniquesList()
    return [technique["TechniqueId"] for technique in techniques_list]


if __name__ == "__main__":
    main()
