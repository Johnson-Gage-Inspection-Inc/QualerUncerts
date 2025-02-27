import requests
import csv
import os

# Create the directory if it doesn't exist
output_dir = 'QualerUncerts/csv'
os.makedirs(output_dir, exist_ok=True)

# Define the headers
headers = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache, must-revalidate",
    "clientrequesttime": "2025-02-27T15:31:17",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not(A:Brand\";v=\"99\", \"Google Chrome\";v=\"133\", \"Chromium\";v=\"133\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "x-requested-with": "XMLHttpRequest"
}

# Create a session
session = requests.Session()

# Set authentication cookies manually (from a valid browser session if needed)
session.cookies.set("ASP.NET_SessionId", "your_session_id_here", domain="jgiquality.qualer.com")
session.cookies.set("Qualer.Employee.Login.SessionId", "your_session_id_here", domain="jgiquality.qualer.com")

# Create the directory if it doesn't exist
output_dir = 'QualerUncerts/csv'
os.makedirs(output_dir, exist_ok=True)

# Define headers (modify if necessary)
headers = {
    "accept": "application/json",
    "x-requested-with": "XMLHttpRequest",
    "user-agent": "Mozilla/5.0",
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

    # Determine the output file name based on the URL
    file_name = url.split('/')[-1].split('?')[0] + '.csv'
    output_file = os.path.join(output_dir, file_name)

    # Write data to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data[0].keys())  # Headers
        for row in data:
            writer.writerow(row.values())

print("Data fetching complete.")


# Define the combinations of serviceGroupId and techniqueId
combinations = [
    (14319, 855),
    # Add more combinations as needed
]

# Fetch data for each combination and save to CSV
for serviceGroupId, techniqueId in combinations:
    url = f"https://jgiquality.qualer.com/ServiceGroupTechnique/UncertaintyBudgets?sort=&group=&filter=&serviceGroupId={serviceGroupId}&techniqueId={techniqueId}"
    response = requests.get(url, headers=headers)
    data = response.json()

    # Determine the output file name based on the URL
    file_name = f"UncertaintyBudgets_{serviceGroupId}_{techniqueId}.csv"
    output_file = os.path.join(output_dir, file_name)

    # Write data to CSV
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write headers
        writer.writerow(data[0].keys())

        # Write rows
        for row in data:
            writer.writerow(row.values())

print("Data has been saved to CSV files in the 'QualerUncerts/csv' directory.")