import csv
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
    "PMCID": 0,
    "PubMed URLs": 0,
    "Unpaywall URL": 0,
    "No Links": 0
}

# Analyze each review
for review in reviews:
    if review["pmc_url"] != "N/A":
        link_types["PMC URL"] += 1
    elif review["pmcid"] != "N/A":
        link_types["PMCID"] += 1
    elif review["pubmed_urls"] != "N/A":
        link_types["PubMed URLs"] += 1
    elif review["unpay_url"] != "N/A":
        link_types["Unpaywall URL"] += 1
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