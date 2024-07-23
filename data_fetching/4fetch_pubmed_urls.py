import requests
import csv
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pmurls.log"),
    ]
)

MAX_RETRIES = 7
MAX_THREADS = 100

def fetch_pubmed_urls(review):
    for retry in range(MAX_RETRIES):
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
                review["pubmed_urls"] = "N/A"
            logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
            return
        except requests.exceptions.HTTPError as http_err:
            if response.status_code == 404:
                review["pubmed_urls"] = "N/A"
                logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
                return
            logging.warning(f"Attempt {retry+1} failed: HTTP error occurred: {http_err}, response: {response.text}")
        except requests.exceptions.ConnectionError as conn_err:
            logging.warning(f"Attempt {retry+1} failed: Connection error occurred: {conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            logging.warning(f"Attempt {retry+1} failed: Timeout error occurred: {timeout_err}")
        except requests.exceptions.RequestException as req_err:
            logging.warning(f"Attempt {retry+1} failed: Request error occurred: {req_err}")
        except ValueError as val_err:
            logging.warning(f"Attempt {retry+1} failed: Value error occurred: {val_err}")
    review["pubmed_urls"] = "FAILURE"
    logging.info(f"{review['pmid']}:{review['pubmed_urls']}")
    
def process_reviews():
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(tqdm(executor.map(lambda review: fetch_pubmed_urls(review),
                               reviews),
                  total=len(reviews),
                  desc="Fetching urls"))  # list forces evaluation of iterator, prevents map from being lazy


with open("pmurls.log", "w"):
    pass # clear

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = [row for row in reader]

process_reviews()

with open("reviews_updated.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=reviews[0].keys())
    writer.writeheader()
    writer.writerows(reviews)