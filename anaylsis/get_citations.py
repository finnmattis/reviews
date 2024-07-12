import os
import re
from xml.etree import ElementTree as ET
from collections import defaultdict

def find_nxml_file(directory):
    for filename in os.listdir(directory):
        if filename.endswith('.nxml'):
            with open(os.path.join(directory, filename), 'r', encoding='utf-8') as file:
                return file.read()
    raise FileNotFoundError("No NXML file found in the specified directory.")

def extract_citations_and_sentences(content):
    # Extract citations
    citation_pattern = r'<mixed-citation.*?</mixed-citation>'
    citations = re.findall(citation_pattern, content, re.DOTALL)
    
    # Extract sentences with citations
    sentence_pattern = r'<p>.*?</p>'
    paragraphs = re.findall(sentence_pattern, content, re.DOTALL)
    
    # Dictionary to store sentences for each citation
    citation_sentences = defaultdict(list)
    
    # Process paragraphs to find citation sentences
    for paragraph in paragraphs:
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        for sentence in sentences:
            citation_ids = re.findall(r'<xref rid="cl21266-bib-(\d+)"', sentence)
            for cit_id in citation_ids:
                clean_sentence = re.sub('<[^<]+>', '', sentence).strip()
                citation_sentences[cit_id].append(clean_sentence)
    
    results = []
    for citation in citations:
        # Parse using ET
        citation = re.sub(r'<ext-link.*?</ext-link>', '', citation)
        root = ET.fromstring(citation)
        
        # Get title
        article_title = root.find('article-title')
        if article_title is not None:
            article_title = article_title.text.strip()
        else:
            article_title = "No title found"

        # Get id
        article_id = root.get('id')
        article_id = re.findall(r'cit-(\d+)', article_id)[0]

        # Get authors
        authors = []
        for string_name in root.findall('string-name'):
            given_names = string_name.find('given-names')
            surname = string_name.find('surname')
            if given_names is not None and surname is not None:
                given_names = given_names.text.strip('.')
                surname = surname.text
                authors.append(f"{surname} {given_names}")
        authors_string = " and ".join(authors)
        
        # Get all sentences where the citation is used
        citation_sentence_list = citation_sentences.get(article_id, ["Citation not found in text"])
        
        # Append
        results.append((article_id, article_title, authors_string, citation_sentence_list))
    
    return results

# Find the NXML file
try:
    content = find_nxml_file("temp")
except FileNotFoundError as e:
    print(f"Error: {e}")
    exit(1)

# Extract citations and sentences
citations_and_sentences = extract_citations_and_sentences(content)

print(f"\nFound {len(citations_and_sentences)} citations:")
for i, citation in enumerate(citations_and_sentences, 1):
    print(f"{i}. ID: {citation[0]}")
    print(f"   Title: {citation[1]}")
    print(f"   Authors: {citation[2]}")
    print(f"   Cited in {len(citation[3])} sentence(s):")
    for j, sentence in enumerate(citation[3], 1):
        print(f"      {j}. {sentence[:100]}..." if len(sentence) > 250 else f"      {j}. {sentence}")
    print()