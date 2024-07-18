import requests
import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pubmed_urls.log"),
        logging.StreamHandler()
    ]
)

MAX_RETRIES = 3

def fetch_pubmed_urls(review):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&id={review['pmid']}&cmd=prlinks&retmode=json"
            response = requests.get(url)
            data = response.json()

            links = []
            if "linksets" in data and data["linksets"]:
                linkset = data["linksets"][0]
                if "idurllist" in linkset and linkset["idurllist"]:
                    for idurlitem in linkset["idurllist"]:
                        if "objurls" in idurlitem:
                            for objurl in idurlitem["objurls"]:
                                link = {
                                    "url": objurl["url"]["value"],
                                    "provider": objurl["provider"]["name"],
                                    "attributes": objurl.get("attributes", []),
                                    "categories": objurl.get("categories", [])
                                }
                                links.append(link)
            if len(links) != 0:
                review["pubmed_urls"] = json.dumps(links)
            else:
                review["pubmed_urls"] = "Not free fulltext"
            logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
            return
        except requests.exceptions.HTTPError as http_err:
            retries += 1
            if response.status_code == 404:
                review["pubmed_urls"] = "404"
                logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
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
    review["pubmed_urls"] = "FAILURE"
    logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
    
def process_reviews():
    with ThreadPoolExecutor(max_workers=100) as executor:
        futures = []
        for review in reviews:
            futures.append(executor.submit(fetch_pubmed_urls, review))

        for future in futures:
            future.result()

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = [row for row in reader]

process_reviews()

with open("reviews.csv", mode="w", newline="") as file:
    fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for review in reviews:
        writer.writerow(review)