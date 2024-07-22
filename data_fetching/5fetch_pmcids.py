import requests
import xml.etree.ElementTree as ET
import csv
from concurrent.futures import ThreadPoolExecutor
import logging
import time
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[
        logging.FileHandler("pmcid.log"),
        logging.StreamHandler()
    ]
)

MAX_RETRIES = 10
BATCH_SIZE = 200
MAX_THREADS = 3  # Adjust based on your system's capabilities

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
                article_id_list = article.find('.//ArticleIdList')

                # Look for the PMCID in the ArticleIdList
                found_pmc = False
                if article_id_list is not None:
                    for article_id in article_id_list.findall('ArticleId'):
                        if article_id.get('IdType') == 'pmc':
                            review["pmcid"] = article_id.text
                            found_pmc = True
                if not found_pmc:
                    review["pmcid"] = "No PMCID found for PMID"
                logging.info(f"{review['pmid']}:{review['pmcid']}")
                
                references = article.findall('.//Reference')
                ref_list = []
                for reference in references:
                    citaiton = reference.find(".//Citation")
                    article_id_list = article.find('.//ArticleIdList')

                    id_list = []
                    if article_id_list is not None:
                        for article_id in article_id_list.findall('ArticleId'):
                            id_list.append((article_id.get('IdType'), article_id.text))
                    ref_list.append((citaiton.text, id_list))
                if len(ref_list) != 0:
                    review["refs"] = json.dumps(ref_list)
                else:
                    review["refs"] = "No refs!"
            return
        else:
            logging.warning(f"Retrying batch {pmids[:50]}... time {retry + 1} reason: {response}")
        time.sleep(15)
    
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

fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "refs"]
with open("reviews_updated.csv", mode="w", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(reviews)
