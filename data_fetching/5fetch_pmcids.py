import requests
import xml.etree.ElementTree as ET
import csv
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pmcid.log"),
        logging.StreamHandler()
    ]
)

MAX_RETRIES = 3
BATCH_SIZE = 200  # NCBI allows up to 200 IDs per request
MAX_THREADS = 5  # Adjust based on your system's capabilities

def fetch_pmcids_batch(batch):
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
                pmid = article.find(".//PMID").text
                pmcid_elem = article.find(".//ArticleId[@IdType='pmc']")
                
                if pmcid_elem is not None:
                    pmcid = pmcid_elem.text
                    logging.info(f"{pmid}:{pmcid}")
                else:
                    pmcid = "Not on PMC"
                    logging.info(f"{pmid}:{pmcid}")
                if review["pmcid"].startswith("PMC"):
                    review["pmcid"] = review["pmcid"][3:]
                else:
                    review["pmcid"] = pmcid # hacky 
            
            return  # Success, exit function
        else:
            logging.warning(f"Retrying batch {pmids[:50]}... time {retry + 1} reason: {response}")
    
    # If we've exhausted all retries
    for review in batch:
        review["pmcid"] = "FAILURE"
        logging.error(f"Failed to fetch PMCID for PMID {review['pmid']}")

def process_reviews(reviews):
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        for i in range(0, len(reviews), BATCH_SIZE):
            batch = reviews[i:i+BATCH_SIZE]
            executor.submit(fetch_pmcids_batch, batch)


with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

process_reviews(reviews)

fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
with open("reviews_updated.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reviews)