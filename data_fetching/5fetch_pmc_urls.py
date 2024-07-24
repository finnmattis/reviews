import requests
import xml.etree.ElementTree as ET
import logging
from concurrent.futures import ThreadPoolExecutor
import csv
from requests.exceptions import RequestException
from tqdm import tqdm
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pmcurls.log"),
    ]
)

MAX_RETRIES = 3
MAX_THREADS = 5

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
                    review["pmc_url"] = "N/A"
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
            return

        except RequestException as e:
            review["pmc_url"] = "FAILURE"
            logging.info(f"{review['pmcid']}:{review['pmc_url']}")
            return
    review["pmc_url"] = "FAILURE"
    logging.info(f"{review['pmcid']}:{review['pmc_url']}")

def process_reviews(reviews):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for review in reviews:
            if review["pmcid"] == "":
                review["pmcid"] = "N/A"
            if urls.get(review["pmcid"]) is not None:
                review["pmc_url"] = urls.get(review["pmcid"])
                continue
            if review["pmcid"] == "N/A":
                review["pmc_url"] = "N/A"
                continue
            futures.append(executor.submit(fetch_pmc_url, review))

        for future in tqdm(futures, total=len(futures), desc="Fetching urls"):
            future.result()

log_file = "pmcurls.log"
info_pattern = re.compile(r'INFO\s+(.*)')

urls = {}

with open(log_file, 'r') as file:
    for line in file:
        match = info_pattern.search(line)
        if match:
            pmid, url = match.group(1).split(':', 1)
            urls[pmid] = url

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

process_reviews(reviews)

with open("reviews_updated.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=reviews[0].keys())
    writer.writeheader()
    writer.writerows(reviews)