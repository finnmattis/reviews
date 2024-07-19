import requests
import xml.etree.ElementTree as ET
import logging
from concurrent.futures import ThreadPoolExecutor
import csv
from requests.exceptions import RequestException

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pmc_url.log"),
        logging.StreamHandler()
    ]
)

MAX_RETRIES = 3
MAX_THREADS = 5  # Adjust based on your system's capabilities

def fetch_pmc_url(review):
    for retry in range(MAX_RETRIES):
        try:
            url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={review['pmcid']}"
            response = requests.get(url)
            response.raise_for_status()
            root = ET.fromstring(response.text)

            error = root.find('.//error')
            if error is not None:
                error_code = error.get('code')
                error_message = error.text
                if error_code == "idIsNotOpenAccess":
                    review["pmc_url"] = "Not OA"
                    logging.info(f"{review['pmcid']}:{review['pmc_url']}")
                    return
                else:
                    logging.error(f"Error for PMC ID {review['pmcid']}: {error_code} - {error_message}")
                    continue

            link = root.find('.//link')
            if link is None:
                logging.warning(f"No link found for PMC ID {review['pmcid']}, retry {retry + 1}")
                continue
            
            ftp_url = link.get('href')
            if not ftp_url:
                logging.warning(f"No FTP URL found for PMC ID {review['pmcid']}, retry {retry + 1}")
                continue

            review["pmc_url"] = ftp_url
            logging.info(f"{review['pmcid']}:{review['pmc_url']}")

        except RequestException as e:
            logging.error(f"Request failed for PMC ID {review['pmcid']}: {str(e)}")
            if retry == MAX_RETRIES - 1:
                logging.error(f"Max retries reached for PMC ID {review['pmcid']}")
                return None

def process_reviews(reviews):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for review in reviews:
            if review["pmcid"] == "Not on PMC":
                logging.info(f"Not on PMC")
                review["pmc_url"] = "Not on PMC"
                continue
            futures.append(executor.submit(fetch_pmc_url, review))

        for future in futures:
            future.result()

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

process_reviews(reviews)

fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
with open("reviews_updated.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reviews)