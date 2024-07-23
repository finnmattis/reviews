import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import json
import sys
import csv
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("metadata.log"),
    ]
)

MAX_RETRIES = 10
BATCH_SIZE = 200
MAX_THREADS = 3

def fetch_pmcids_batch(batch, ref_list):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    pmids = ",".join(review["pmid"] for review in batch)
    
    params = {
        "db": "pubmed",
        "id": pmids,
        "retmode": "xml"
    }
    
    for retry in range(MAX_RETRIES):
        response = requests.get(base_url, params=params)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)

            articles = root.findall(".//PubmedArticle")
            for article, review in zip(articles, batch):
                # ... (rest of the processing code remains the same)
                logging.info(f"Got metadata for pmid {review['pmid']}")
            return
        else:
            logging.warning(f"Retrying batch {pmids[:50]}... time {retry + 1} reason: {response}")
        time.sleep(10)
    
    for review in batch:
        keys = ["pmcid", "doi", "title", "completed", "revised", "authors", "journal", "num_refs", "topics"]
        for key in keys:
            review[key] = "FAILURE"
        ref_list.append(f"{review['pmid']}<|sep|>FAILURE")
        logging.error(f"Failed to fetch metadata for pmid {review['pmid']}")

def process_reviews(reviews, ref_list):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        list(tqdm(executor.map(lambda batch: fetch_pmcids_batch(batch, ref_list),
                               [reviews[i:i+BATCH_SIZE] for i in range(0, len(reviews), BATCH_SIZE)]),
                  total=len(reviews)//BATCH_SIZE + (1 if len(reviews) % BATCH_SIZE else 0),
                  desc="Fetching metadata")) # list forces evaluation of iterator, prevents map from being lazy

with open("metadata.log", "w"): # clear file
    pass

try:
    with open('ids.txt', 'r') as file:
        pmids = [line.strip() for line in file.readlines()]
except FileNotFoundError:
    print("ids.txt not found - run previous script")
    sys.exit()

reviews = []
for pmid in pmids:
    reviews.append({"pmid": pmid})
ref_list = []
process_reviews(reviews, ref_list)

with open("reviews_updated.csv", 'w', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=reviews[0].keys())
    writer.writeheader()
    writer.writerows(reviews)
with open("refs.txt", 'w') as file:
        for string in ref_list:
            file.write(string + '\n')