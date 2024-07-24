import requests
from bs4 import BeautifulSoup
import re
import time
import csv
import random

def get_pmc_html(review, max_retries=3, delay=1):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    } # Avoid 403
    
    # fetch the HTML content
    pmc_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/{review['pmcid'][3:]}/" # get rid of PMC prefix
    
    for attempt in range(max_retries):
        try:
            response = requests.get(pmc_url, headers=headers)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise ConnectionError(f"Failed to fetch HTML for PMC ID {review['pmcid']} after {max_retries} attempts: {str(e)}")
            time.sleep(delay)
    return response.content

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

while True: 
    review = random.choice(reviews)
    if review["pmcid"] != "N/A" and review["pmc_url"] == "N/A":
        print(review["pmcid"])
        break

html = get_pmc_html(review)

with open(f"{review['pmcid']}.txt", "w") as file:
    file.write(str(html))