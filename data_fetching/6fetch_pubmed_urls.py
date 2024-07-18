import requests
import xml.etree.ElementTree as ET
import logging
from concurrent.futures import ThreadPoolExecutor
import csv

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
    pmcid = review['pmcid'][3:]
    for retry in range(MAX_RETRIES):
        url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id={pmcid}"
        response = requests.get(url)
        response.raise_for_status()
        root = ET.fromstring(response.text)

        link = root.find('.//link')
        if link is None:
            logging.warning(f"Retrying pmcid {pmcid} retry {retry}")
            continue
        ftp_url = link.get('href')
        if not ftp_url:
            logging.warning(f"Retrying pmcid {pmcid} {retry}")
            continue

def process_reviews(reviews) -> None:
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = []
        for review in reviews:
            if review["pmcid"] == "Not on PMC":
                review["pmc_url"] = "Not on PMC"
                continue
            futures.append(executor.submit(fetch_pmc_url, review))

        for future in futures:
            future.result()

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

process_reviews(reviews)

# fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
# with open("reviews_updated.csv", mode="w", newline="") as file:
#     writer = csv.DictWriter(file, fieldnames=fieldnames)
#     writer.writeheader()
#     writer.writerows(reviews)