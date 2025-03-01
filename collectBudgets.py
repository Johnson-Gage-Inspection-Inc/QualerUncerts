import requests
import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
from sqlalchemy import create_engine
from getpass import getpass
from time import sleep
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm

# Create the directory if it doesn't exist
output_dir = "csv"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "CompleteUncertaintyBudgets.csv")

# Load environment variables from .env file
load_dotenv()

# Set up database connection
engine = create_engine("postgresql://postgres:postgres@192.168.1.177:5432/qualer")

# Set up Selenium WebDriver
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run in headless mode
chrome_options.add_argument("--log-level=3")
driver = webdriver.Chrome(options=chrome_options)


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


def getUncertaintyBudgets(uncertaintyBudgetId, retries=3):
    """Fetch UncertaintyBudgets JSON with retry for stale element issues."""
    url = f"https://jgiquality.qualer.com/UncertaintyComponent/List?UncertaintyBudgetId={uncertaintyBudgetId}"

    for attempt in range(retries):
        try:
            driver_get(url)
            data = driver.find_element(By.TAG_NAME, "pre").text
            return json.loads(data).get("uncertaintyComponents", [])
        except StaleElementReferenceException:
            if attempt < retries - 1:
                print(
                    f"Stale element encountered. Retrying ({attempt + 1}/{retries})..."
                )
                sleep(2)  # Small delay before retrying
            else:
                raise  # Raise the error if all retries fail


def query_uncertainty_budgets():
    """Fetch Uncertainty Budget IDs from the database."""
    data = pd.read_sql(
        'SELECT "UncertaintyBudgetId" FROM public.uncertainty_budgets', engine
    )
    return data["UncertaintyBudgetId"].tolist()


def main():
    # Perform login
    login()

    # Extract cookies for requests session
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])

    # Fetch Uncertainty Budget IDs
    UncertaintyBudgetIds = query_uncertainty_budgets()

    # Ensure the CSV file starts fresh
    if os.path.exists(output_file):
        os.remove(output_file)

    for uncertaintyBudgetId in tqdm(
        UncertaintyBudgetIds, desc="Fetching Uncertainty Budgets"
    ):
        uncertainty_budgets = getUncertaintyBudgets(uncertaintyBudgetId)
        for row in uncertainty_budgets:
            row["UncertaintyBudgetId"] = uncertaintyBudgetId

        if uncertainty_budgets:
            df = pd.DataFrame(uncertainty_budgets)
            df.to_csv(
                output_file,
                mode="a",
                header=not os.path.exists(output_file),
                index=False,
            )

    print("Data has been saved to CSV files in the 'csv' directory.")


if __name__ == "__main__":
    main()
    driver.quit()
    print("Done.")
