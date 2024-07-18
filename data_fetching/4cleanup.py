import re
import csv
import requests
import json

MAX_RETRIES = 3
def fetch_pubmed_urls(review):
    print("HI")
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
            return
        except requests.exceptions.HTTPError as http_err:
            retries += 1
            if response.status_code == 404:
                review["pubmed_urls"] = "404"
                return
    review["pubmed_urls"] = "FAILURE"


################################################################################


log_file = "pubmed_urls.log"
info_pattern = re.compile(r'INFO\s+(.*)')

urls = {}

with open(log_file, 'r') as file:
    for line in file:
        match = info_pattern.search(line)
        if match:
            pmid, url = match.group(1).split(':', 1)
            urls[pmid] = url

print(len(urls))

with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = [row for row in reader]

for review in reviews:
    url = urls.get(review["pmid"], None)
    if url:
        review["pubmed_urls"] = url
    else:
        fetch_pubmed_urls(review)

for review in reviews:
    if review["pubmed_urls"] == "FAILURE":
        print("FAILURE")
    elif review["pubmed_urls"] == "":
        print("missing")

with open("reviews.csv", mode="w", newline="") as file:
    fieldnames = ["pmid", "title", "authors", "citation", "author", "journal", "pub_year", "pub_date", "blank1", "blank2", "doi", "license", "unpay_url", "pubmed_urls", "pmcid", "pmc_url"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for review in reviews:
        writer.writerow(review)