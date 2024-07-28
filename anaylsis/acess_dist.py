import csv
import json
import matplotlib.pyplot as plt

#review["pmc_url"] > review["pmcid"] > reviews["pubmed_urls"] > reviews["unpay_url"]

# Read the CSV file
with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

import csv
import matplotlib.pyplot as plt

# Read the CSV file
with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

# Initialize counters for each link type
link_types = {
    "PMC URL": 0,
    # "PMCID": 0,
    "Unpaywall URL (non-pdf)": 0,
    "PubMed URLs (non-pdf)": 0,
    "Unpaywall URL (pdf)": 0,
    "PubMed URLs (pdf)": 0,
    "No Links": 0
}

for review in reviews:
    if review["pmc_url"] != "N/A":
        link_types["PMC URL"] += 1
        continue
    # if review["pmcid"] != "N/A":
    #     link_types["PMCID"] += 1
    #
    if review["unpay_url"] != "N/A"and "pdf" not in review["unpay_url"]:
        link_types["Unpaywall URL (non-pdf)"] += 1
        continue
    if review["pubmed_urls"] != "N/A":
        non_pdf = False
        urls = json.loads(review["pubmed_urls"])
        for url in urls:
            if "pdf" not in url["url"]:
                non_pdf = True
        if non_pdf:
            link_types["PubMed URLs (non-pdf)"] += 1
            continue
    if review["unpay_url"] != "N/A":
        link_types["Unpaywall URL (pdf)"] += 1
    elif review["pubmed_urls"] != "N/A":
        link_types["PubMed URLs (pdf)"] += 1
    else:
        link_types["No Links"] += 1

plt.figure(figsize=(10, 8))
plt.pie(link_types.values(), labels=link_types.keys(), autopct='%1.1f%%', startangle=90)
plt.title("Distribution of Best Available Link Types in Reviews")
plt.axis('equal')

plt.show()

print("Link Type Distribution:")
for link_type, count in link_types.items():
    print(f"{link_type}: {count}")