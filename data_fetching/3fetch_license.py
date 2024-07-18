import csv
import requests
from concurrent.futures import ThreadPoolExecutor
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("license.log"),
        logging.StreamHandler()
    ]
)

EMAIL = "planto73@harkenpretty.com"
MAX_RETRIES = 3

def fetch_license(review, email):
    url = f"https://api.unpaywall.org/v2/{review['DOI']}"
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.get(url, params={"email": email}, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            data = response.json()
            best_oa_location = data.get("best_oa_location")
            review["url"] = best_oa_location.get("url") if best_oa_location else "No url found"
            review["license"] = best_oa_location.get("license") if best_oa_location else "No license found"
            # None type does not go into the csv
            if review["license"] == None:
                review["license"] = "No license found"
            logging.info(f'{review["url"]}, {review["license"]}')
            return
        except requests.exceptions.HTTPError as http_err:
            retries += 1
            if response.status_code == 404:
                review["url"] = "404"
                review["license"] = "404"
                logging.info(f'{review["url"]}, {review["pdf_url"]}, {review["license"]}')
                return
            logging.warning(f"Attempt {retries} failed: HTTP error occurred: {http_err}, response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            retries += 1
            logging.warning(f"Attempt {retries} failed: Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            retries += 1
            logging.warning(f"Attempt {retries} failed: Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            retries += 1
            logging.warning(f"Attempt {retries} failed: Request error occurred: {req_err}")
        except ValueError as val_err:
            retries += 1
            logging.warning(f"Attempt {retries} failed: Value error occurred: {val_err}")
    review["url"] = "FAILURE"
    review["license"] = "FAILURE"
    logging.info(f'{review["url"]}, {review["license"]}')

def fetch_licenses():
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for review in reviews:
            futures.append(executor.submit(fetch_license, review, EMAIL))

        for future in futures:
            future.result()

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = [row for row in reader]
fetch_licenses()

with open("reviews.csv", mode="w", newline="") as file:
    fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for review in reviews:
        writer.writerow(review)
