import csv
import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import sys
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("license.log"),
    ]
)

EMAIL = "planto73@harkenpretty.com"
MAX_RETRIES = 3
MAX_THREADS = 100

def fetch_license(review, email):
    if review["doi"] == "N/A":
        review["license"] = "N/A"
        review["unpay_url"] = "N/A"
        
    url = f"https://api.unpaywall.org/v2/{review['doi']}"
    for retry in range(MAX_RETRIES):
        try:
            response = requests.get(url, params={"email": email}, timeout=10)

            if response.status_code == 200:
                data = response.json()
                best_oa_location = data.get("best_oa_location")
                review["license"] = best_oa_location.get("license", "N/A") if best_oa_location else "N/A"
                review["unpay_url"] = best_oa_location.get("url", "N/A") if best_oa_location else "N/A"
                if review["license"] == None: # None is not merely a default value returned by get but rather in the data returned
                    review["license"] = "N/A"
                logging.info(f'{review["pmid"]}:{review["license"]},{review["unpay_url"]}')
                return
            elif response.status_code == 404:
                review["license"] = "N/A"
                review["unpay_url"] = "N/A"
                logging.info(f'{review["pmid"]}:{review["license"]},{review["unpay_url"]}')
                return
            else:
                logging.warning(f"Retrying batch {review['pmid']}... time {retry + 1} reason: {response}")
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"Attempt {retry+1} failed: HTTP error occurred: {http_err}, response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            logging.warning(f"Attempt {retry+1} failed: Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            logging.warning(f"Attempt {retry+1} failed: Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            logging.warning(f"Attempt {retry+1} failed: Request error occurred: {req_err}")
        except ValueError as val_err:
            logging.warning(f"Attempt {retry+1} failed: Value error occurred: {val_err}")
        
    review["license"] = "FAILURE"
    review["unpay_url"] = "FAILURE"
    logging.info(f'{review["pmid"]}:{review["license"]},{review["unpay_url"]}')

def fetch_licenses():
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(tqdm(executor.map(lambda review: fetch_license(review, EMAIL),
                               reviews),
                  total=len(reviews),
                  desc="Fetching licenses"))  # list forces evaluation of iterator, prevents map from being lazy

with open("license.log", "w"): # clear file
    pass

try:
    with open("reviews.csv", mode="r") as file:
        reader = csv.DictReader(file)
        reviews = [row for row in reader]
except FileNotFoundError:
    print("reviews.csv not found - run previous scripts")
    sys.exit()

fetch_licenses()

with open("reviews_updated.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=reviews[0].keys())
    writer.writeheader()
    writer.writerows(reviews)