import csv
import matplotlib.pyplot as plt

# options: nothing, unpaywall, pubmed links, PMC ftp

# Read the CSV file
with open("reviews.csv", mode="r") as file:
    reader = csv.DictReader(file)
    reviews = list(reader)

# Count reviews on PMC
num_pmc = sum(1 for review in reviews if review["pmcid"] != "Not on PMC")
num_not_pmc = len(reviews) - num_pmc

# Data for pie chart
labels = ['On PMC', 'Not on PMC']
sizes = [num_pmc, num_not_pmc]
colors = ['#ff9999', '#66b3ff']
explode = (0.1, 0)  # explode 1st slice

# Create pie chart
plt.figure(figsize=(10, 7))
plt.pie(sizes, explode=explode, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=90, shadow=True)

# Equal aspect ratio ensures that pie is drawn as a circle
plt.axis('equal')

plt.title("Distribution of Reviews on PMC")
plt.show()

# Print the exact numbers
print(f"Reviews on PMC: {num_pmc}")
print(f"Reviews not on PMC: {num_not_pmc}")
print(f"Total reviews: {len(reviews)}")